import json
import random
import yaml
from datetime import datetime, timedelta
import os
from saas_service_mappings import (
    PLAN_REVENUE_MULTIPLIER,
    PLAN_USAGE_MULTIPLIER,
    INDUSTRY_REVENUE_MULTIPLIER
)
from aws_service_mappings import SERVICE_USAGE_MULTIPLIER
from aws_service_mappings import (
    SERVICE_REGION_MAP,
    RESOURCE_ID_PATTERNS,
    USAGE_TYPE_MAP,
    get_rate_for_service
)

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_field_value(field, context, prev_record=None, reference_pools=None):
    # Handle type: datetime
    if field['type'] == 'datetime':
        # Use min/max from field, but set max to end of current month if not already dynamic
        min_str = field.get('min', "2024-01-01T00:00:00")
        max_str = field.get('max', None)
        if not max_str or max_str == 'dynamic' or (isinstance(max_str, str) and max_str.startswith('dynamic:')):
            # Compute end of current month
            today = datetime.today()
            if today.month == 12:
                next_month = datetime(today.year + 1, 1, 1)
            else:
                next_month = datetime(today.year, today.month + 1, 1)
            end_of_month = next_month - timedelta(seconds=1)
            max_str = end_of_month.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            min_dt = datetime.strptime(min_str, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            min_dt = datetime.strptime(min_str[:19], "%Y-%m-%dT%H:%M:%S")
        try:
            max_dt = datetime.strptime(max_str, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            max_dt = datetime.strptime(max_str[:19], "%Y-%m-%dT%H:%M:%S")
        delta = max_dt - min_dt
        rand_seconds = random.randint(0, int(delta.total_seconds()))
        dt = min_dt + timedelta(seconds=rand_seconds)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    # Handle type: reference (external value pool)
    if field['type'] == 'reference':
        if reference_pools is None:
            reference_pools = {}
        ref_file = field['reference_file']
        ref_field = field['reference_field']
        unique = field.get('unique', False)
        pool_key = f"{ref_file}:{ref_field}:unique" if unique else ref_file
        if pool_key not in reference_pools:
            # Load the pool from file
            if not os.path.exists(ref_file):
                raise FileNotFoundError(f"Reference file not found: {ref_file}")
            with open(ref_file, 'r') as f:
                pool = json.load(f)
            if unique:
                # Shuffle for unique assignment
                random.shuffle(pool)
            reference_pools[pool_key] = pool.copy()
        pool = reference_pools[pool_key]
        if unique:
            if not pool:
                raise ValueError(f"No more unique values available in {ref_file} for {ref_field}")
            entry = pool.pop()
        else:
            entry = random.choice(pool)
        return entry[ref_field]
    # Handle type: faker
    if field['type'] == 'faker':
        if fake is None:
            raise ImportError("Faker library is not installed. Run 'pip install faker'.")
        faker_method = field.get('faker_method')
        if not faker_method or not hasattr(fake, faker_method):
            raise ValueError(f"Invalid or missing faker_method: {faker_method}")
        return getattr(fake, faker_method)()
    # Handle type: string with pattern and components
    if field['type'] == 'string' and 'pattern' in field and 'components' in field:
        components = {}
        for cname, cdef in field['components'].items():
            # Recursively call get_field_value for each component
            comp_val = get_field_value(cdef, context, prev_record)
            components[cname] = comp_val
        try:
            return field['pattern'].format(**components)
        except Exception:
            return None
    # Handle type: choice (with optional weights)
    if field['type'] == 'choice':
        # Multi-field consistency for key fields
        if field['name'] == 'service':
            # Pick a service at random from those with mappings
            return random.choice(list(SERVICE_REGION_MAP.keys()))
        if field['name'] == 'region' and prev_record and 'service' in prev_record:
            service = prev_record['service']
            return random.choice(SERVICE_REGION_MAP.get(service, ['us-east-1']))
        if field['name'] == 'usage_type' and prev_record and 'service' in prev_record:
            service = prev_record['service']
            return random.choice(USAGE_TYPE_MAP.get(service, ['BoxUsage']))
        if field['name'] == 'resource_id' and prev_record and 'service' in prev_record:
            service = prev_record['service']
            pattern_func = RESOURCE_ID_PATTERNS.get(service)
            if pattern_func:
                return pattern_func()
        # Default: original logic
        if 'values_by_company' in field and prev_record:
            company = prev_record.get('company')
            return random.choice(field['values_by_company'][company])
        values = field['values']
        weights = field.get('weights')
        if weights:
            return random.choices(values, weights=weights, k=1)[0]
        return random.choice(values)
    # Handle type: int/float with optional by_service and usage multiplier
    if field['type'] in ['int', 'float']:
        min_v = field.get('min', 0)
        max_v = field.get('max', 100)
        multiplier = 1.0
        topic = context.get('topic') if context else None
        # SaaS: plan-based multipliers
        if topic and 'saas' in topic:
            if field['name'] == 'monthly_fee' and prev_record and 'plan' in prev_record:
                plan = prev_record['plan']
                multiplier = PLAN_REVENUE_MULTIPLIER.get(plan, 1.0)
            if field['name'] == 'usage_events' and prev_record and 'plan' in prev_record:
                plan = prev_record['plan']
                multiplier = PLAN_USAGE_MULTIPLIER.get(plan, 1.0)
            if field['name'] == 'annual_revenue_musd' and prev_record and 'industry' in prev_record:
                industry = prev_record['industry']
                multiplier = INDUSTRY_REVENUE_MULTIPLIER.get(industry, 1.0)
        # AWS: service-based multipliers
        elif 'by_service' in field and prev_record:
            service = prev_record.get('service')
            svc_cfg = field['by_service'].get(service)
            if svc_cfg:
                min_v = svc_cfg.get('min', min_v)
                max_v = svc_cfg.get('max', max_v)
            if field['name'] == 'usage_quantity' and service in SERVICE_USAGE_MULTIPLIER:
                multiplier = SERVICE_USAGE_MULTIPLIER[service]
        if field['type'] == 'int':
            return int(random.randint(min_v, max_v) * multiplier)
        else:
            return round(random.uniform(min_v, max_v) * multiplier, 2)
    # Handle type: date
    if field['type'] == 'date':
        def to_datetime(val):
            if isinstance(val, datetime):
                return val
            if hasattr(val, 'year') and hasattr(val, 'month') and hasattr(val, 'day'):
                return datetime(val.year, val.month, val.day)
            return datetime.strptime(str(val), "%Y-%m-%d")
        start = to_datetime(field['start'])
        end_val = field.get('end')
        if (
            not end_val
            or (isinstance(end_val, str) and (end_val == 'dynamic' or end_val.startswith('dynamic:')))
        ):
            # Compute end of current month
            today = datetime.today()
            if today.month == 12:
                next_month = datetime(today.year + 1, 1, 1)
            else:
                next_month = datetime(today.year, today.month + 1, 1)
            end = next_month - timedelta(days=1)
        else:
            end = to_datetime(end_val)
        delta = (end - start).days
        date = start + timedelta(days=random.randint(0, delta))
        # If time_format is specified, add random time and use that format
        if 'time_format' in field:
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            date = date.replace(hour=hour, minute=minute, second=second)
            return date.strftime(field['time_format'])
        return date.strftime("%Y-%m-%d")
    # Handle type: formula (supports referencing previous fields, date math, and output formatting)
    if field['type'] == 'formula' and prev_record:
        # Multi-field consistency: enforce cost = usage_quantity * rate for cost field
        if field['name'] == 'cost' and 'usage_quantity' in prev_record and 'service' in prev_record and 'usage_type' in prev_record:
            rate = get_rate_for_service(prev_record['service'], prev_record['usage_type'])
            prev_record['rate'] = rate
            cost = prev_record['usage_quantity'] * rate
            return round(cost, 2)
        formula = field.get('formula', '')
        # Inject rate/base_fee from by_service if present and not already in prev_record
        if 'by_service' in field:
            service = prev_record.get('service')
            svc_cfg = field['by_service'].get(service)
            if svc_cfg:
                if 'rate' in svc_cfg:
                    prev_record['rate'] = svc_cfg['rate']
                if 'base_fee' in svc_cfg:
                    prev_record['base_fee'] = svc_cfg['base_fee']
        local_vars = prev_record.copy()
        # Always parse any date/datetime string fields to datetime objects for formula evaluation
        for k, v in local_vars.items():
            if isinstance(v, str):
                # Try to parse as datetime (ISO format or date only)
                try:
                    local_vars[k] = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S')
                except Exception:
                    try:
                        local_vars[k] = datetime.strptime(v, '%Y-%m-%d')
                    except Exception:
                        pass
        try:
            # Patch: support datetime + int (days) in formula by replacing '+' with a helper
            def add_dt(a, b):
                if isinstance(a, datetime) and isinstance(b, int):
                    return a + timedelta(days=b)
                if isinstance(b, datetime) and isinstance(a, int):
                    return b + timedelta(days=a)
                return a + b
            # Replace '+' with add_dt for date math
            # Only patch if formula contains '+'
            if '+' in formula:
                # Split formula on '+' and evaluate each side, then add with add_dt
                parts = formula.split('+')
                if len(parts) == 2:
                    left = eval(parts[0].strip(), {"__builtins__": None}, local_vars)
                    right = eval(parts[1].strip(), {"__builtins__": None}, local_vars)
                    result = add_dt(left, right)
                else:
                    # Fallback to normal eval for more complex formulas
                    result = eval(formula, {"__builtins__": None}, local_vars)
            else:
                result = eval(formula, {"__builtins__": None}, local_vars)
            if isinstance(result, datetime):
                fmt = field.get('output_format') or field.get('time_format') or '%Y-%m-%dT%H:%M:%S'
                return result.strftime(fmt)
            if field['name'] == 'variance_pct':
                return round(result, 4)
            if isinstance(result, float):
                return round(result, 2)
            return result
        except Exception:
            return None
    # Default fallback
    return None


def generate_records_from_config(config, num_records=10000, upward_drift=0.005, spike_prob=0.02, spike_min=2.0, spike_max=10.0, spend_multiplier=1.0, s3_partition_fields=None):
    records = []
    fields = config['fields']
    output_fields = [f['name'] for f in fields if not f['name'].endswith('_faker')]
    if s3_partition_fields is None:
        s3_partition_fields = config.get('s3_partition_fields', [])
    # Pre-load all reference pools
    reference_pools = {}
    for field in fields:
        if field.get('type') == 'reference':
            ref_file = field['reference_file']
            ref_field = field['reference_field']
            unique = field.get('unique', False)
            pool_key = f"{ref_file}:{ref_field}:unique" if unique else ref_file
            if pool_key not in reference_pools:
                if not os.path.exists(ref_file):
                    raise FileNotFoundError(f"Reference file not found: {ref_file}")
                with open(ref_file, 'r') as f:
                    pool = json.load(f)
                if unique:
                    random.shuffle(pool)
                reference_pools[pool_key] = pool.copy()
    # State for continuity: {(account_id, service, resource_id): {field: last_value}}
    continuity_state = {}
    for _ in range(num_records):
        record = {}
        key_fields = {}
        # Pre-populate key fields for continuity
        for field in fields:
            if field['name'] in ('account_id', 'service', 'resource_id'):
                value = get_field_value(field, config.get('context', {}), record, reference_pools)
                record[field['name']] = value
                key_fields[field['name']] = value
        state_key = (key_fields.get('account_id'), key_fields.get('service'), key_fields.get('resource_id'))
        last_vals = continuity_state.get(state_key, {})
        # Generate other fields, using continuity for usage_quantity and cost
        for field in fields:
            fname = field['name']
            if fname in ('account_id', 'service', 'resource_id'):
                continue
            if fname in ('usage_quantity', 'cost') and last_vals.get(fname) is not None:
                # Upward drift
                drift = upward_drift * last_vals[fname]
                sigma = 0.05 * last_vals[fname] if last_vals[fname] else 1.0
                new_val = max(0, last_vals[fname] + random.normalvariate(drift, sigma))
                # Occasionally inject a sharp spike
                if random.random() < spike_prob:
                    spike = random.uniform(spike_min, spike_max)
                    new_val = last_vals[fname] * spike
                # For cost, round to 2 decimals and apply spend multiplier
                if fname == 'cost':
                    new_val = round(new_val * spend_multiplier, 2)
                record[fname] = new_val
            else:
                value = get_field_value(field, config.get('context', {}), record, reference_pools)
                # Apply spend multiplier to cost field
                if fname == 'cost' and value is not None:
                    value = round(value * spend_multiplier, 2)
                record[fname] = value
        # Update continuity state
        if state_key not in continuity_state:
            continuity_state[state_key] = {}
        for fname in ('usage_quantity', 'cost'):
            if fname in record:
                continuity_state[state_key][fname] = record[fname]
        # S3-style partition path
        if s3_partition_fields:
            parts = []
            for pf in s3_partition_fields:
                val = record.get(pf)
                if val is None:
                    continue
                # Try to parse as date or datetime, but only use date part for partitioning
                date_obj = None
                if isinstance(val, str):
                    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                        try:
                            date_obj = datetime.strptime(val, fmt)
                            break
                        except Exception:
                            continue
                if date_obj:
                    parts.append(f"year={date_obj.year}")
                    parts.append(f"month={date_obj.month:02d}")
                    parts.append(f"day={date_obj.day:02d}")
                else:
                    parts.append(f"{pf}={val}")
            record['s3_path'] = "/".join(parts) + "/" if parts else ""
        # Only include output fields (exclude *_faker fields)
        output_record = {k: v for k, v in record.items() if k in output_fields}
        if s3_partition_fields:
            output_record['s3_path'] = record.get('s3_path', "")
        records.append(output_record)
    return records


def main():
    import argparse
    import pandas as pd
    parser = argparse.ArgumentParser(description="Generate dummy data from topic config.")
    parser.add_argument("--config", type=str, required=True, help="Path to topic YAML config file")
    parser.add_argument("--num-records", type=int, default=10000, help="Number of records to generate")
    parser.add_argument("--output", type=str, required=False, help="Output file path (json, csv, or parquet). Defaults to ~/Desktop/<topic>.json")
    parser.add_argument("--output-type", type=str, choices=["json", "csv", "parquet", "jsonl"], default=None, help="Output file type (json, csv, parquet, jsonl). If not set, inferred from file extension.")
    parser.add_argument("--s3-partition-fields", type=str, default=None, help="Comma-separated list of fields to use for S3-style partition path (e.g. shipped_date,region)")
    parser.add_argument("--upward-drift", type=float, default=0.005, help="Upward drift per step (default: 0.005, or 0.5%)")
    parser.add_argument("--spike-prob", type=float, default=0.02, help="Probability of a spike per record (default: 0.02, or 2%)")
    parser.add_argument("--spike-min", type=float, default=2.0, help="Minimum spike multiplier (default: 2.0)")
    parser.add_argument("--spike-max", type=float, default=10.0, help="Maximum spike multiplier (default: 10.0)")
    parser.add_argument("--spend-multiplier", type=float, default=1.0, help="Global spend multiplier for all costs (default: 1.0, lower for smaller demo spend, e.g. 0.15 for $100M max)")
    args = parser.parse_args()
    config = load_config(args.config)
    s3_partition_fields = None
    if args.s3_partition_fields:
        s3_partition_fields = [f.strip() for f in args.s3_partition_fields.split(",") if f.strip()]
    records = generate_records_from_config(
        config,
        num_records=args.num_records,
        upward_drift=args.upward_drift,
        spike_prob=args.spike_prob,
        spike_min=args.spike_min,
        spike_max=args.spike_max,
        spend_multiplier=args.spend_multiplier,
        s3_partition_fields=s3_partition_fields
    )

    # Debug: print first 5 records to check partition field values
    print("Sample generated records (first 5):")
    for rec in records[:5]:
        print(rec)

    # Determine output path and type
    topic = config.get('topic', 'output')
    # Determine output type first
    output_type = args.output_type
    output_path = args.output if args.output else None
    if output_type is None:
        if output_path and output_path.endswith(".jsonl"):
            output_type = "jsonl"
        elif output_path and output_path.endswith(".json"):
            output_type = "json"
        elif output_path and output_path.endswith(".csv"):
            output_type = "csv"
        elif output_path and output_path.endswith(".parquet"):
            output_type = "parquet"
        else:
            output_type = "json"
    # Set default output path based on type if not provided
    if not output_path:
        ext = output_type
        if ext == "jsonl":
            ext = "jsonl"
        elif ext == "json":
            ext = "json"
        elif ext == "csv":
            ext = "csv"
        elif ext == "parquet":
            ext = "parquet"
        else:
            ext = "json"
        output_path = os.path.expanduser(f"~/Desktop/{topic}.{ext}")

    if s3_partition_fields and output_type in ("csv", "parquet"):
        from collections import defaultdict
        partitioned_records = defaultdict(list)
        for rec in records:
            s3_path = rec.get('s3_path', '')
            partitioned_records[s3_path].append(rec)
        # Debug: print partition paths and record counts
        print("Partition summary:")
        for s3_path, recs in list(partitioned_records.items())[:10]:
            print(f"{s3_path}: {len(recs)} records")
        print(f"Total partitions: {len(partitioned_records)}")
        base_dir, base_file = os.path.split(output_path)
        base_file_noext = os.path.splitext(base_file)[0]
        ext = output_type
        topic_dir = os.path.join(base_dir, topic)
        if topic_dir:
            os.makedirs(topic_dir, exist_ok=True)
        for s3_path, recs in partitioned_records.items():
            # Remove s3_path from records for output
            for r in recs:
                if 's3_path' in r:
                    r.pop('s3_path')
            part_dir = os.path.join(topic_dir, s3_path)
            os.makedirs(part_dir, exist_ok=True)
            part_file = os.path.join(part_dir, f"{base_file_noext}.{ext}")
            df = pd.DataFrame(recs)
            if output_type == "csv":
                df.to_csv(part_file, index=False)
            elif output_type == "parquet":
                df.to_parquet(part_file, index=False)
        print(f"Wrote {len(partitioned_records)} partitioned files under {topic_dir or '.'}")
    else:
        if output_type == "json":
            with open(output_path, "w") as f:
                json.dump(records, f, indent=2)
        elif output_type == "jsonl":
            with open(output_path, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")
        elif output_type == "csv":
            df = pd.DataFrame(records)
            df.to_csv(output_path, index=False)
        elif output_type == "parquet":
            df = pd.DataFrame(records)
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported output type: {output_type}")
        print(f"Generated {len(records)} records for topic '{topic}' in {output_path} (type: {output_type})")


if __name__ == "__main__":
    main()
