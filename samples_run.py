
# Modular, config-driven data generator
import json
import random
import yaml
from datetime import datetime, timedelta
import os
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
        # Use min/max from field, default to now +/- 365 days if missing
        min_str = field.get('min', "2024-01-01T00:00:00")
        max_str = field.get('max', "2025-01-01T00:00:00")
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
        if 'values_by_company' in field and prev_record:
            company = prev_record.get('company')
            return random.choice(field['values_by_company'][company])
        values = field['values']
        weights = field.get('weights')
        if weights:
            return random.choices(values, weights=weights, k=1)[0]
        return random.choice(values)
    # Handle type: int/float with optional by_service
    if field['type'] in ['int', 'float']:
        min_v = field.get('min', 0)
        max_v = field.get('max', 100)
        if 'by_service' in field and prev_record:
            service = prev_record.get('service')
            svc_cfg = field['by_service'].get(service)
            if svc_cfg:
                min_v = svc_cfg.get('min', min_v)
                max_v = svc_cfg.get('max', max_v)
        if field['type'] == 'int':
            return random.randint(min_v, max_v)
        else:
            return round(random.uniform(min_v, max_v), 2)
    # Handle type: date
    if field['type'] == 'date':
        def to_datetime(val):
            if isinstance(val, datetime):
                return val
            if hasattr(val, 'year') and hasattr(val, 'month') and hasattr(val, 'day'):
                return datetime(val.year, val.month, val.day)
            return datetime.strptime(str(val), "%Y-%m-%d")
        start = to_datetime(field['start'])
        end = to_datetime(field['end'])
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
        formula = field.get('formula', '')
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


def generate_records_from_config(config, num_records=10000):
    records = []
    fields = config['fields']
    output_fields = [f['name'] for f in fields if not f['name'].endswith('_faker')]
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
                # Trend logic: new = last + N(0, sigma) + drift
                drift = 0.0
                sigma = 0.05 * last_vals[fname] if last_vals[fname] else 1.0
                if fname == 'usage_quantity':
                    drift = -0.005 * last_vals[fname]  # small downward drift
                elif fname == 'cost':
                    drift = -0.005 * last_vals[fname]
                new_val = max(0, last_vals[fname] + random.normalvariate(drift, sigma))
                # For cost, round to 2 decimals
                if fname == 'cost':
                    new_val = round(new_val, 2)
                record[fname] = new_val
            else:
                value = get_field_value(field, config.get('context', {}), record, reference_pools)
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
                # Try to parse as date
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
    parser.add_argument("--output-type", type=str, choices=["json", "csv", "parquet"], default=None, help="Output file type (json, csv, parquet). If not set, inferred from file extension.")
    parser.add_argument("--s3-partition-fields", type=str, default=None, help="Comma-separated list of fields to use for S3-style partition path (e.g. shipped_date,region)")
    args = parser.parse_args()
    config = load_config(args.config)
    s3_partition_fields = None
    if args.s3_partition_fields:
        s3_partition_fields = [f.strip() for f in args.s3_partition_fields.split(",") if f.strip()]
    # Inject partition fields into function as attribute
    generate_records_from_config.s3_partition_fields = s3_partition_fields
    records = generate_records_from_config(config, num_records=args.num_records)

    # Determine output path and type
    topic = config.get('topic', 'output')
    default_output = os.path.expanduser(f"~/Desktop/{topic}.json")
    output_path = args.output if args.output else default_output
    output_type = args.output_type
    if output_type is None:
        if output_path.endswith(".json"):
            output_type = "json"
        elif output_path.endswith(".csv"):
            output_type = "csv"
        elif output_path.endswith(".parquet"):
            output_type = "parquet"
        else:
            output_type = "json"  # Default

    if output_type == "json":
        with open(output_path, "w") as f:
            json.dump(records, f, indent=2)
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
