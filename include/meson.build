if get_option('build_cpp').enabled()
  cpp_header = custom_target('cpp_header', command: generator_command, input: files('vkfl.hpp.in'),
                             output: '@BASENAME@', build_by_default: true)
  vkfl_cpp_files += cpp_header
endif
if get_option('build_c').enabled()
  c_header = custom_target('c_header', command: generator_command, input: files('vkfl.h.in'),
                           output: '@BASENAME@', build_by_default: true)
  vkfl_c_files += c_header
endif
