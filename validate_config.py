
import yaml
import sys
import os
import json


def validate_yaml_config(config_path):
    errors = []
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        errors.append(f"YAML parse error: {e}")
        return errors

    if 'fields' not in config or not isinstance(config['fields'], list):
        errors.append("Missing or invalid 'fields' list.")
        return errors

    field_names = set()
    for i, field in enumerate(config['fields']):
        if 'name' not in field:
            errors.append(f"Field {i} missing 'name'.")
            continue
        if field['name'] in field_names:
            errors.append(f"Duplicate field name: {field['name']}")
        field_names.add(field['name'])
        if 'type' not in field:
            errors.append(f"Field {field['name']} missing 'type'.")
            continue
        t = field['type']
        if t == 'choice':
            if 'values' not in field or not isinstance(field['values'], list):
                errors.append(f"Field {field['name']} of type 'choice' missing 'values' list.")
            if 'weights' in field and len(field['weights']) != len(field['values']):
                errors.append(f"Field {field['name']} weights length does not match values length.")
        if t == 'faker' and 'faker_method' not in field:
            errors.append(f"Field {field['name']} of type 'faker' missing 'faker_method'.")
        if t == 'reference':
            if 'reference_file' not in field or 'reference_field' not in field:
                errors.append(f"Field {field['name']} of type 'reference' missing 'reference_file' or 'reference_field'.")
            else:
                if not os.path.exists(field['reference_file']):
                    errors.append(f"Reference file not found: {field['reference_file']} for field {field['name']}")
                else:
                    try:
                        with open(field['reference_file'], 'r') as rf:
                            pool = json.load(rf)
                        if not pool or field['reference_field'] not in pool[0]:
                            errors.append(f"reference_field {field['reference_field']} not found in {field['reference_file']} for field {field['name']}")
                    except Exception as e:
                        errors.append(f"Error reading reference file {field['reference_file']}: {e}")
        if t == 'string' and 'pattern' in field and 'components' not in field:
            errors.append(f"Field {field['name']} has pattern but no components.")
        if t == 'formula' and 'formula' not in field:
            errors.append(f"Field {field['name']} of type 'formula' missing 'formula' property.")
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_config.py <config.yaml>")
        sys.exit(1)
    config_path = sys.argv[1]
    errors = validate_yaml_config(config_path)
    if errors:
        print(f"Validation failed for {config_path}:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"{config_path} is valid.")


if __name__ == "__main__":
    main()
