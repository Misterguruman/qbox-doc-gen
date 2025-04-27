from lib.ManifestReader import Manifest
import os
import re

class Event:
    def __init__(self, name: str, args: list[str], annotations: list[tuple[str, str]]):
        self.name = name
        self.args = args
        self.annotations = annotations

    def __repr__(self):
        return f"Event(name={self.name}, args={self.args}, annotations={self.annotations})"

class Callback:
    def __init__(self, name: str, args: list[str], annotations: list[tuple[str, str]]):
        self.name = name
        self.args = args
        self.annotations = annotations

    def __repr__(self):
        return f"Callback(name={self.name}, args={self.args}, annotations={self.annotations})"

class Script:
    def __init__(self, script_path: str):
        self.script_path = script_path
        self.exists = os.path.exists(script_path)
        self.events = []
        self.callbacks = []
        self.commands = []
        self.exports = []

        if self.exists:
            self.events = self._get_events()
            self.callbacks = self._get_callbacks()

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



class Resource: 
    def __init__(self, resource_path: str):
        self.resource_path = resource_path
        self.manifest = Manifest(resource_path)

        self.server_scripts = [Script(os.path.join(resource_path, '\\'.join([x for x in script.split('/')]))) for script in self.manifest.server_scripts]
        for script in self.server_scripts:
            print(script.script_path)
            print(script.exists)
            for event in script.events:
                print(event)

            for callback in script.callbacks:
                print(callback)
