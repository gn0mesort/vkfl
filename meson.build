project(
  'vkfl',
  [ 'c', 'cpp' ],
  version: '1.0.0',
  license: 'LGPL-3.0',
  default_options: [
    'c_std=c18',
    'c_link_args=-Wl,-rpath=$ORIGIN/../lib',
    'cpp_std=c++20',
    'cpp_link_args=-Wl,-rpath=$ORIGIN/../lib',
    'warning_level=3',
    'b_ndebug=if-release',
    'b_pie=true'
  ]
)

specification = '--spec=@0@'.format(get_option('specification'))
api_version = '--api=@0@'.format(get_option('api'))
extensions = '--extensions='
foreach extension : get_option('extensions')
  extensions += '@0@,'.format(extension)
endforeach
generator_command = [ find_program('tools/generate.py'), specification, api_version, extensions, '@INPUT@',
                      '@OUTPUT@' ]

header = custom_target('header', command: generator_command, input: 'include/vkfl.hpp.in',
                       output: '@BASENAME@')
source = custom_target('source', command: generator_command, input: 'src/vkfl.cpp.in',
                       output: '@BASENAME@')

vkfl_dep = declare_dependency(sources: [ header, source ], dependencies: dependency('vulkan'))

subdir('test')
