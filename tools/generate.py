#!/usr/bin/env python3
from collections import OrderedDict
from urllib.request import urlopen
from xml.etree import ElementTree as etree
import re
import os
import sys
from argparse import ArgumentParser

def parse_xml(path):
    file = urlopen(path) if path.startswith('http') else open(path, 'r')
    with file:
        return etree.parse(file)

def to_snake_case(text: str):
    return re.sub(r'([A-Z]+)', r'_\1', text).lower()

def is_descendent(vktypes, name, base):
    if name == base:
        return True
    current = vktypes.get(name)
    if not current:
        return False
    parents = current.get('parent')
    if not parents:
        return False
    return any([ is_descendent(vktypes, parent, base) for parent in parents.split(',') ])

def identify_group(vktypes, command):
    vkglobalpfns = [ 'vkEnumerateInstanceVersion', 'vkEnumerateInstanceExtensionProperties',
                     'vkEnumerateInstanceLayerProperties', 'vkCreateInstance', 'vkGetInstanceProcAddr' ]
    name = command.findtext('proto/name')
    owner = command.findtext('param[1]/type')
    for pfn in vkglobalpfns:
        if name == pfn:
            return 'global'
    if name != 'vkGetDeviceProcAddr' and is_descendent(vktypes, owner, 'VkDevice'):
        return 'device'
    return 'instance'

def commands_str(commands_by_requirement):
    result = ''
    for requirement in commands_by_requirement:
        # result += f'#if {requirement}{os.linesep}'
        commands = commands_by_requirement[requirement]
        for command in commands:
            name = command['name']
            result += f'\t\t{name[2:]},{os.linesep}'
        # result += f'#endif{os.linesep}'
    return result.strip().expandtabs(2)

def command_count_str(commands_by_requirement):
    result = 0
    for requirement in commands_by_requirement:
        result += len(commands_by_requirement[requirement])
    return str(result)

def global_loader_str(commands_by_requirement):
    result = ''
    for requirement in commands_by_requirement:
        # tmp = f'#if {requirement}{os.linesep}'
        tmp = ''
        commands = commands_by_requirement[requirement]
        cmd_count = 0
        for command in commands:
            if command['loaded_from'] == 'global' and command['name'] != 'vkGetInstanceProcAddr':
                name = command['name']
                tmp += f'\t\tm_pfns[static_cast<std::size_t>(command::{name[2:]})] = '
                tmp += f'context_loader(nullptr, "{name}");{os.linesep}'
                cmd_count += 1
        # tmp += f'#endif{os.linesep}'
        if cmd_count > 0:
            result += tmp
    return result.rstrip().expandtabs(2)

def instance_loader_str(commands_by_requirement):
    result = ''
    for requirement in commands_by_requirement:
        tmp = '' # f'#if {requirement}{os.linesep}'
        commands = commands_by_requirement[requirement]
        cmd_count = 0
        for command in commands:
            if command['loaded_from'] == 'instance':
                name = command['name']
                tmp += f'\t\tm_pfns[static_cast<std::size_t>(command::{name[2:]})] = '
                tmp += f'context_loader(context, "{name}");{os.linesep}'
                cmd_count += 1
        # tmp += f'#endif{os.linesep}'
        if cmd_count > 0:
            result += tmp
    return result.rstrip().expandtabs(2)

def device_loader_str(commands_by_requirement):
    result = ''
    for requirement in commands_by_requirement:
        tmp = '' # f'#if {requirement}{os.linesep}'
        commands = commands_by_requirement[requirement]
        cmd_count = 0
        for command in commands:
            if command['loaded_from'] == 'device':
                name = command['name']
                tmp += f'\t\tm_pfns[static_cast<std::size_t>(command::{name[2:]})] = '
                tmp += f'context_loader(context, "{name}");{os.linesep}'
                cmd_count += 1
        # tmp += f'#endif{os.linesep}'
        if cmd_count > 0:
            result += tmp
    return result.rstrip().expandtabs(2)

def undef_str(undefs):
    result = ''
    for undef_name in undefs:
        result += f'#if defined({undef_name}){os.linesep}'
        result += f'\t#undef {undef_name}{os.linesep}'
        result += f'#endif{os.linesep}'
    return result.rstrip().expandtabs(2)

def aliasfns_str(commands_by_requirement):
    result = ''
    for requirement in commands_by_requirement:
        result += f'#if {requirement}{os.linesep}'
        commands = commands_by_requirement[requirement]
        for command in commands:
            name = command['name']
            result += f'\tusing {to_snake_case(name)[3:]} = PFN_{name};{os.linesep}'
        result += f'#endif{os.linesep}'
    return result.strip().expandtabs(2)

def header_version_str(tree):
    return tree.find('types/type[name="VK_HEADER_VERSION"]').find('name').tail.strip()

VK_SPEC = 'https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/xml/vk.xml'

parser = ArgumentParser()
parser.add_argument('--spec', type=str, default=VK_SPEC,
                    help='Specifies the URI to load the XML Vulkan specification from.')
parser.add_argument('--extensions', type=str, default='all',
                    help='A comma separated list of Vulkan extensions to include in the loader.' +
                         'This may also be the special value \"all\".')
parser.add_argument('--api', type=str, default='latest',
                    help='The latest Vulkan API version to include in the loader (i.e. 1.0, 1.1, 1.2, etc.).'
                         'This may also be the special value \"latest\".')
parser.add_argument('INPUT', type=str)
parser.add_argument('OUTPUT', type=str)

args = parser.parse_args()
tree = parse_xml(args.spec)
exts = set(args.extensions.split(','))
api = args.api
if api != 'latest':
    api = float(api)

vktypes = { }
for vktype in tree.findall('types/type'):
    name = vktype.findtext('name')
    vktypes[name] = vktype

vkcommands = { }
for vkcommand in tree.findall('commands/command'):
    alias = vkcommand.get('alias')
    name = vkcommand.get('name') if alias else vkcommand.findtext('proto/name')
    vkcommands[name] = { }
    vkcommands[name]['name'] = name
    vkcommands[name]['element'] = vkcommand
    vkcommands[name]['requirement'] = [ ]
    vkcommands[name]['used_by'] = set()
    vkcommands[name]['is_alias'] = True if alias else False
    vkcommands[name]['loaded_from'] = identify_group(vktypes, vkcommand)

for vkfeature in tree.findall('feature'):
    name = vkfeature.get('name')
    version = float(vkfeature.get('number'))
    for command in vkfeature.findall('require/command'):
        command_name = command.get('name')
        vkcommands[command_name]['used_by'].add(name)
        vkcommands[command_name]['requirement'].append(f'defined({name})')

for vkextension in tree.findall('extensions/extension'):
    name = vkextension.get('name')
    for requirement in vkextension.findall('require'):
        subrequirement = requirement.get('extension')
        subrequirement = subrequirement if subrequirement else requirement.get('feature')
        compound = f'defined({name}) && defined({subrequirement})' if subrequirement else f'defined({name})'
        for command in requirement.findall('command'):
            command_name = command.get('name')
            vkcommands[command_name]['used_by'].add(name)
            vkcommands[command_name]['requirement'].append(compound)

undefs = set()
for vkfeature in tree.findall('feature'):
    version = float(vkfeature.get('number'))
    name = vkfeature.get('name')
    for vkcommand in vkcommands:
        if api != 'latest' and version - api > 0.00001 and name in vkcommands[vkcommand]['used_by']:
            vkcommands[vkcommand]['used_by'].remove(name)
            undefs.add(name)
for vkextension in tree.findall('extensions/extension'):
    name = vkextension.get('name')
    for vkcommand in vkcommands:
        if not ('all' in exts) and not (name in exts) and name in vkcommands[vkcommand]['used_by']:
            vkcommands[vkcommand]['used_by'].remove(name)
            undefs.add(name)

for vkcommand in vkcommands:
    final_requirement = ''
    if len(vkcommands[vkcommand]['used_by']) == 0:
        final_requirement = '(0)'
    else:
        final_requirement = f'({vkcommands[vkcommand]["requirement"][0]})'
        for requirement in vkcommands[vkcommand]['requirement'][1:]:
            final_requirement += f' || ({requirement})'
    vkcommands[vkcommand]['requirement'] = final_requirement

commands_by_requirement = OrderedDict()
for vkcommand in sorted(vkcommands):
    requirement = vkcommands[vkcommand]['requirement']
    if not commands_by_requirement.get(requirement):
        commands_by_requirement[requirement] = [ ]
    commands_by_requirement[requirement].append(vkcommands[vkcommand])
if '(0)' in commands_by_requirement:
    commands_by_requirement.pop('(0)')

text = ''
with open(args.INPUT, 'rb') as file:
    text = str(file.read(), 'utf-8')
text = text.replace('@undefs@', undef_str(undefs))
text = text.replace('@commands@', commands_str(commands_by_requirement))
text = text.replace('@commands_count@', command_count_str(commands_by_requirement))
text = text.replace('@header_version@', header_version_str(tree))
text = text.replace('@load_global@', global_loader_str(commands_by_requirement))
text = text.replace('@load_instance@', instance_loader_str(commands_by_requirement))
text = text.replace('@load_device@', device_loader_str(commands_by_requirement))
text = text.replace('@aliasfns@', aliasfns_str(commands_by_requirement))
with open(args.OUTPUT, 'wb') as file:
    file.truncate()
    file.write(bytes(text, 'utf-8'))
