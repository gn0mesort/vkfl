project(
  'vkfl',
  [ 'c', 'cpp' ],
  version: '1.2.0',
  license: 'Apache-2.0',
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

generator_args = [ ]
if get_option('specification') != 'default'
  generator_args += '--spec=@0@'.format(get_option('specification'))
endif
if get_option('api') != 'latest'
  generator_args += '--api=@0@'.format(get_option('api'))
endif
extension_arr = get_option('extensions')
if extension_arr.length() != 0
  if extension_arr[0] != 'all'
    extensions = '--extensions='
    foreach extension : get_option('extensions')
      extensions += '@0@,'.format(extension)
    endforeach
    generator_args += extensions
  endif
else
  generator_args += '--extensions=""'
endif
if get_option('enable_extra_defines')
  generator_args += '--generate-extra-defines'
endif
generator_command = [ find_program('tools/generate.py'), generator_args, '@INPUT@', '@OUTPUT@' ]
doc_deps = [ ]
if get_option('enable_cpp')
  cpp_header = custom_target('cpp_header', command: generator_command, input: 'include/vkfl.hpp.in',
                             output: '@BASENAME@', build_by_default: true)
  cpp_source = custom_target('cpp_source', command: generator_command, input: 'src/vkfl.cpp.in',
                             output: '@BASENAME@', build_by_default: true)
  vkfl_cpp_dep = declare_dependency(sources: [ cpp_header, cpp_source ])
  doc_deps += [ cpp_header, cpp_source ]
endif
if get_option('enable_c')
  c_header = custom_target('c_header', command: generator_command, input: 'include/vkfl.h.in', output: '@BASENAME@',
                           build_by_default: true)
  c_source = custom_target('c_source', command: generator_command, input: 'src/vkfl.c.in', output: '@BASENAME@',
                           build_by_default: true)
  vkfl_c_dep = declare_dependency(sources: [ c_header, c_source ])
  doc_deps += [ c_header, c_source ]
endif

doxygen = find_program('doxygen', required: false, disabler: true)
vkfl_docs = run_target('documentation', command: [ doxygen, files('Doxyfile') ], depends: doc_deps)

vulkan_dep = dependency('vulkan', required: false, disabler: true)

if get_option('enable_tests')
  subdir('test')
endif
if get_option('enable_examples')
  subdir('examples')
endif
