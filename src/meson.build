if get_option('build_cpp').enabled()
  cpp_source = custom_target('cpp_source', command: generator_command, input: files('vkfl.cpp.in'),
                             output: '@BASENAME@', build_by_default: true)
  vkfl_cpp_files += cpp_source
endif
if get_option('build_c').enabled()
  c_source = custom_target('c_source', command: generator_command, input: files('vkfl.c.in'),
                           output: '@BASENAME@', build_by_default: true)
  vkfl_c_files += c_source
endif
