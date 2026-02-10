import os
import re
import json
import apphelpers
import hashlib
from flask import render_template, request, abort
import apphelpers, test_runner
from appstate import nav
BASE_INCLUDE_DIR = "/usr/share/cc65/include/"








def register_routes(app):
    @app.route('/projectB')
    def projbtest():
        return "Hello from ProjectB"
    


    @nav("Proj-C-Seach")
    @app.route("/seasearch", methods=["GET"])
    def seasearch():
        query = request.args.get("q", "").strip().lower()
        results = []

        test_runner.reload_tests()

        for modname in apphelpers.testfile_registry:
            parts = modname.split(".")
            base_dir = os.path.join("/testsrc/sourcedir", *parts[:-1])

            if not os.path.isdir(base_dir):
                continue

            for root, _, files in os.walk(base_dir):
                for fname in files:
                    if not fname.endswith(".c"):
                        continue

                    cpath = os.path.join(root, fname)

                    try:
                        parsed = parse_c_file(cpath)
                    except Exception:
                        continue

                    for func_name, meta in parsed["functions"].items():
                        if meta.get("checksum") is None:
                            continue
                            
                        if query and query not in func_name.lower():
                            continue

                        results.append({
                            "function": func_name,
                            "args": meta.get("args"),
                            "module": modname,
                            "path": cpath,
                            "checksum": meta.get("checksum")
                        })

        return render_template("seasearch.html", query=query, results=results)


    @nav("CC65_headerfiles")
    @app.route('/libsearch')
    def libsearch():
        all_data = []
        
        # Recursive Walk
        for root, dirs, files in os.walk(BASE_INCLUDE_DIR):
            for file in files:
                if file.endswith(('.h', '.c')):
                    full_path = os.path.join(root, file)
                    all_data.extend(parse_header_file(full_path))
        print(json.dumps(all_data, indent=4))
        return render_template('libsearch.html', data=all_data)


def parse_c_file(filename):
    includes = set()
    functions = {}

    with open(filename, "r") as f:
        code = f.read()

    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    includes.update(re.findall(r'#include\s*<([^>]+)>', code))

    pattern = r'((\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{([^}]*)\})'
    func_matches = re.findall(pattern, code, flags=re.DOTALL)

    for full_text, ret_type, func_name, args, body in func_matches:
        arg_count = 0 if args.strip() in ("", "void") else len([a for a in args.split(',') if a.strip()])
        
        checksum = hashlib.md5(full_text.strip().encode('utf-8')).hexdigest()
        
        functions[func_name] = {
            "args": arg_count, 
            "calls": [], 
            "checksum": checksum
        }

        for call, call_args in re.findall(r'\b(\w+)\s*\(([^;{}]*)\)', body):
            call_arg_count = 0 if call_args.strip() == "" else len([a for a in call_args.split(',') if a.strip()])
            if call not in functions:
                functions[call] = {"args": call_arg_count, "calls": [], "checksum": None}
            functions[func_name]["calls"].append(call)

    return {"includes": includes, "functions": functions}


def extract_name(definition):
    # Remove array brackets and values [10]
    temp = re.sub(r'\[.*?\]', '', definition)
    # Remove parameter list (...)
    if '(' in temp:
        temp = temp.split('(')[0]
    
    # Cleanup trailing chars
    temp = temp.replace('*', ' ').replace(';', '').replace('{', '').strip()
    
    # The name is usually the last token
    tokens = temp.split()
    if tokens:
        return tokens[-1]
    return "unknown"


def parse_header_file(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {filepath}: {e}")
        return []

    struct_regex = re.compile(
        r'struct\s+(\w+)\s*\{([^}]*)\}\s*;',
        re.MULTILINE | re.DOTALL
    )

    generic_regex = re.compile(
        r'(?P<def>'
        r'(?:^[\t ]*)'
        r'(?:unsigned|signed|struct|extern|const|volatile|void|int|char|long|short|typedef)'
        r'[^;{]*?[;{]'
        r')'
        r'(?P<cmt>'
        r'(?:\s*(?:/\*[\s\S]*?\*/|//.*))?'
        r')',
        re.MULTILINE | re.VERBOSE
    )

    # Parse structs first
    for match in struct_regex.finditer(content):
        struct_name = match.group(1)
        struct_body = match.group(2)
        line_num = content.count('\n', 0, match.start()) + 1
        members = {}
        for line in struct_body.split(';'):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                var_type = " ".join(parts[:-1])
                var_name = parts[-1].replace('*', '').strip()
                members[var_name] = var_type
        results.append({
            "name": struct_name,
            "type": "struct",
            "definition": match.group(0).rstrip(),
            "members": members,
            "comment": "",
            "path": filepath,
            "line": line_num
        })

    # Parse functions/variables separately
    for match in generic_regex.finditer(content):
        definition_raw = match.group('def').strip()
        if "struct" in definition_raw:
            continue
        comment_raw = match.group('cmt')
        line_num = content.count('\n', 0, match.start('def')) + 1
        clean_comment = ""
        if comment_raw:
            clean_comment = re.sub(r'/\*+|\*+/|^//|^\s*\* ?', '', comment_raw.strip(), flags=re.MULTILINE).strip()
        if definition_raw.startswith('#') or len(definition_raw) < 5:
            continue

        # Extract function arguments
        params = []
        if '(' in definition_raw and ')' in definition_raw:
            param_list = definition_raw.split('(', 1)[1].rsplit(')', 1)[0].strip()
            if param_list and param_list != "void":
                for p in param_list.split(','):
                    p = p.strip()
                    parts = p.split()
                    if len(parts) >= 2:
                        param_type = " ".join(parts[:-1])
                        param_name = parts[-1].replace('*', '').strip()
                        params.append({"type": param_type, "arg": param_name})
                    else:
                        params.append({"type": parts[0], "arg": ""})  # fallback for single token

        results.append({
            "name": extract_name(definition_raw),
            "type": "func/var",
            "definition": definition_raw.rstrip(),
            "params": params,
            "comment": clean_comment,
            "path": filepath,
            "line": line_num
        })


    return results
