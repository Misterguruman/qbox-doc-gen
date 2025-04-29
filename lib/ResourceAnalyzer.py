from lib.ManifestReader import Manifest
import os
import re
import json
import shutil
import itertools
from textwrap import dedent

class Event:
    def __init__(self, name: str, args: list[str], annotations: list[tuple[str, str]]):
        self.name = name
        self.args = args
        self.annotations = annotations

    def __repr__(self):
        return f"Event(name={self.name}, args={self.args}, annotations={self.annotations})"
    
    def to_mdx(self):
        mdx = dedent(f"""\
        ### {self.name.split(':')[-1]}
        
        Triggered when a player.. #TODO: finish
        ```lua
        RegisterNetEvent('{self.name}', function({', '.join(self.args)}) end)
        ```
        """
        )

        for key, value in self.annotations:
            mdx += f"- {key}: {value}\n"
        mdx += "---"

        return mdx

class Callback:
    def __init__(self, name: str, args: list[str], annotations: list[tuple[str, str]]):
        self.name = name
        self.args = args
        self.annotations = annotations

    def __repr__(self):
        return f"Callback(name={self.name}, args={self.args}, annotations={self.annotations})"
    
    def to_mdx(self):
        mdx = dedent(f"""\
        ### {self.name.split(':')[-1]}
        
        Triggered when a player.. #TODO: finish
        ```lua
        lib.callback.await('{self.name}', false, {', '.join(self.args)})
        ```
        """
        )

        for key, value in self.annotations:
            mdx += f"- {key}: {value}\n"
        mdx += "---"

        return mdx

class Export:
    def __init__(self, name: str, args: list[str], arg_types: dict[str, str], return_type: str, resource_name: str):
        self.name = name
        self.args = args
        self.arg_types = arg_types
        self.return_type = return_type
        self.resource_name = resource_name

    def __repr__(self):
        return f"Export(name={self.name}, args={self.args}, arg_types={self.arg_types}, return_type={self.return_type})"
    
    def to_mdx(self):
        mdx = dedent(f"""\
        ### {self.name.split(':')[-1]}
        
        Triggered when a player.. #TODO: finish
        ```lua
        exports.{self.resource_name}:{self.name}({', '.join(self.args)})
        ```
        """
        )

        for key, value in self.arg_types.items():
            mdx += f"- {key}: {value}\n"
        mdx += "---"

        return mdx

class Command:
    def __init__(self, name: str, help_text: str, params: list[dict[str, str]], parent):
        self.name = name
        self.help_text = help_text
        self.params = params
        self.script = parent

    def __repr__(self):
        return f"Command(name={self.name}, help_text={self.help_text}, params={self.params})"
    
    def to_mdx(self):
        mdx = dedent(f"""\
        ### {self.name}
        ```lua
        exports.{self.resource_name}:{self.name}({', '.join(self.args)})
        ```
        """
        )

        for key, value in self.arg_types.items():
            mdx += f"- {key}: {value}\n"
        mdx += "---"

        return mdx

class Script:
    def __init__(self, script_path: str, resource_name: str):
        self.resource_name = resource_name
        self.script_path = script_path
        self.exists = os.path.exists(script_path)
        self.events = []
        self.callbacks = []
        # self.commands = []
        self.exports = []

        if self.exists:
            self.events = self._get_events()
            self.callbacks = self._get_callbacks()
            # self.commands = self._get_commands()
            self.exports = self._get_exports()

        else:
            print(f"Unable to find script {script_path} in resource {resource_name}")

    def _get_events(self):
        lua_source = open(self.script_path, 'r').read()
        block_re = re.compile(
            r'''
            (
                (?:^\s*---@param[^\n]*\n)*  # -- zero or more param lines
            )
            ^\s*RegisterNetEvent\(
                \s*['"]([^'"]+)['"]\s*,       # -- event name
                \s*function\s*\(([^)]*)\)     # -- arg list
            ''',
            re.MULTILINE | re.VERBOSE
        )
        param_re = re.compile(r'^---@param\s+(\w+)\s+([^\s]+)', re.MULTILINE)
        results = [] 
        for doc_block, event_name, raw_args in block_re.findall(lua_source):
            params = param_re.findall(doc_block)
            arg_names = [a.strip() for a in raw_args.split(',') if a.strip()]

            results.append(Event(event_name, arg_names, params))

        return results
    
    def _get_callbacks(self):
        lua_source = open(self.script_path, 'r').read()
        block_re = re.compile(
            r'''
            (
                (?:^\s*---@param[^\n]*\n)*  # -- zero or more param lines
            )
            ^lib\.callback\.register\(
                \s*['"]([^'"]+)['"]\s*,       # -- event name
                \s*function\s*\(([^)]*)\)     # -- arg list
            ''',
            re.MULTILINE | re.VERBOSE
        )
        param_re = re.compile(r'^---@param\s+(\w+)\s+([^\s]+)', re.MULTILINE)
        results = [] 
        for doc_block, event_name, raw_args in block_re.findall(lua_source):
            params = param_re.findall(doc_block)
            arg_names = [a.strip() for a in raw_args.split(',') if a.strip()]

            results.append(Callback(event_name, arg_names, params))

        return results
    
    def _get_commands(self):
        lua_source = open(self.script_path, 'r').read()
        add_cmd_re = re.compile(
            r'''
            lib\.addCommand\(\s*                  
                ['"]([^'"]+)['"]\s*,\s*           
                \{                                
                    (?:(?!\}\s*,?\s*function).)*? 
                    (?:                           
                        \bhelp\s*=\s*([^,}]+)     
                    )?                            
                    (?:                           
                        .*?                       
                        \bparams\s*=\s*{          
                        (                         
                            (?:                   
                                [^{}]             
                            | \{[^{}]*\}          
                            )*
                        )                         
                        }                         
                    )?                            
                    .*?                           
                \}                                
            \s*,\s*function                       
            ''',
            re.DOTALL | re.VERBOSE
        )

        param_re = re.compile(
            r'''
            \{[^{}]*?                        
                \bname\s*=\s*['"]([^'"]+)['"]
                [^{}]*?                      
                \btype\s*=\s*['"]([^'"]+)['"]
                [^{}]*?                      
                \bhelp\s*=\s*([^,}\n]+)      
                [^{}]*?                      
            \}                               
            ''',
            re.DOTALL | re.VERBOSE
        )

        result = []

        for cmd, help_val, params_block in add_cmd_re.findall(lua_source):
            params = [
                {'name': n, 'type': t, 'help': h.strip()}
                for n, t, h in param_re.findall(params_block or '')
            ]
            result.append(Command(cmd, help_val.strip(), params))

        return result
    
    def _get_exports(self):
        lua_source = open(self.script_path, 'r').read()

        # ① grab all exports and all functions once
        export_re = re.compile(r'^[ \t]*exports\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\w+)\s*\)', re.MULTILINE)
        func_re   = re.compile(r'''(?P<ann>(?:^[ \t]*---@.*\n)*)^[ \t]*(?:local[ \t]+)?function[ \t]+(?P<name>\w+)[ \t]*\((?P<args>[^\)]*)\)''', re.MULTILINE)
        param_re  = re.compile(r'^[ \t]*---@param[ \t]+(\w+)[ \t]+([^\s]+)', re.MULTILINE)
        return_re = re.compile(r'^[ \t]*---@return[ \t]+([^\s]+)',           re.MULTILINE)

        exports = [(m.start(), m.group(1), m.group(2)) for m in export_re.finditer(lua_source)]
        funcs   = [(m.start(), m.group('name'), m.group('args'), m.group('ann')) for m in func_re.finditer(lua_source)]

        results = []          # one dict per export

        for exp_pos, export_name, func_var in exports:
            # pick the closest *earlier* function whose name matches the variable in exports(...)
            candidates = [f for f in funcs if f[0] < exp_pos and f[1] == func_var]
            if not candidates:
                continue
            _, _, arg_string, ann_block = candidates[-1]

            arg_list   = [a.strip() for a in arg_string.split(',') if a.strip()]
            param_dict = dict(param_re.findall(ann_block))
            ret_match  = return_re.search(ann_block)
            ret_type   = ret_match.group(1) if ret_match else None

            results.append(Export(export_name, arg_list, param_dict or None, ret_type, self.resource_name))

        return results

class Resource: 
    def __init__(self, resource_path: str):
        self.resource_path = resource_path
        self.manifest = Manifest(resource_path)

        if self.manifest.english_locale and self.manifest.english_locale_path:
            with open(self.manifest.english_locale_path, encoding='utf-8') as fh:
                self.locale_data = json.load(fh)

        self.server_scripts = [Script(os.path.join(resource_path, '\\'.join([x for x in script.split('/')])), self.manifest.resource) for script in self.manifest.server_scripts]
        self.client_scripts = [Script(os.path.join(resource_path, '\\'.join([x for x in script.split('/')])), self.manifest.resource) for script in self.manifest.client_scripts]
        self.shared_scripts = [Script(os.path.join(resource_path, '\\'.join([x for x in script.split('/')])), self.manifest.resource) for script in self.manifest.shared_scripts]

    def export(self):
        export_directory = os.path.join(os.getcwd(), 'export', self.manifest.resource)
        if os.path.exists(export_directory):
            shutil.rmtree(export_directory, True)
        
        os.makedirs(export_directory)
        
        self._export_events(export_directory)
        self._export_exports(export_directory)
        self._export_callbacks(export_directory)

    def _export_events(self, export_directory):
        event_export_directory = os.path.join(export_directory, 'events')
        server_events = itertools.chain.from_iterable([x.events for x in self.server_scripts])
        client_events = itertools.chain.from_iterable([x.events for x in self.client_scripts])
        shared_events = itertools.chain.from_iterable([x.events for x in self.shared_scripts])

        if not any(server_events or client_events or shared_events):
            print("No events found, exiting..")
            return
        
        os.makedirs(event_export_directory)

        self._write_to_file(os.path.join(event_export_directory, 'server.mdx'), server_events)
        self._write_to_file(os.path.join(event_export_directory, 'client.mdx'), client_events)
        self._write_to_file(os.path.join(event_export_directory, 'shared.mdx'), shared_events)

    def _export_exports(self, export_directory):
        event_export_directory = os.path.join(export_directory, 'exports')
        server_exports = itertools.chain.from_iterable([x.exports for x in self.server_scripts])
        client_exports = itertools.chain.from_iterable([x.exports for x in self.client_scripts])
        shared_exports = itertools.chain.from_iterable([x.exports for x in self.shared_scripts])

        if not any(server_exports or client_exports or shared_exports):
            print("No exports found, exiting..")
            return
        
        os.makedirs(event_export_directory)

        self._write_to_file(os.path.join(event_export_directory, 'server.mdx'), server_exports)
        self._write_to_file(os.path.join(event_export_directory, 'client.mdx'), client_exports)
        self._write_to_file(os.path.join(event_export_directory, 'shared.mdx'), shared_exports)

    def _export_callbacks(self, export_directory):
        event_export_directory = os.path.join(export_directory, 'callbacks')
        server_callbacks = itertools.chain.from_iterable([x.callbacks for x in self.server_scripts])
        client_callbacks = itertools.chain.from_iterable([x.callbacks for x in self.client_scripts])
        shared_callbacks = itertools.chain.from_iterable([x.callbacks for x in self.shared_scripts])

        if not any(server_callbacks or client_callbacks or shared_callbacks):
            print("No callbacks found, exiting..")
            return
        
        os.makedirs(event_export_directory)

        self._write_to_file(os.path.join(event_export_directory, 'server.mdx'), server_callbacks)
        self._write_to_file(os.path.join(event_export_directory, 'client.mdx'), client_callbacks)
        self._write_to_file(os.path.join(event_export_directory, 'shared.mdx'), shared_callbacks)

    def _write_to_file(self, file_path, content):
        if content:
            file_handle = open(file_path, 'w+')
            for item in content:
                file_handle.write(item.to_mdx())