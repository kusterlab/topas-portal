from enum import Enum
import inspect


def enum_to_js(enum_cls, include_keys=None):
    """
    Convert a Python Enum to a JS Object.freeze string.
    Optionally filter keys via include_keys.
    """
    lines = []

    for member in enum_cls:
        if include_keys and member.name not in include_keys:
            continue
        lines.append(f"  {member.name}: '{member.value}'")

    if len(lines) == 0:
        return ""

    body = ",\n".join(lines)
    return f"export const {enum_cls.__name__} = Object.freeze({{\n{body}\n}})\n"


def export_enums(modules, output_file):
    """
    Find all Enum classes in a module and export them to JS.
    """
    enums = []
    for module in modules:
        enums.extend(
            [
                obj
                for _, obj in inspect.getmembers(module)
                if inspect.isclass(obj) and issubclass(obj, Enum)
            ]
        )

    with open(output_file, "w") as f:
        f.write("// this is an automatically generated file that mirrors the enums in flask-backend/topas_portal/constants.py\n\n")
        for enum_cls in enums:
            js = enum_to_js(enum_cls)
            f.write(js + "\n")


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    import topas_portal.data_type as data_type
    import topas_portal.constants as constants

    export_enums([data_type, constants], "../vue-frontend/src/constants.js")
