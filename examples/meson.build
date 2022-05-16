if get_option('build_examples').enabled()
  partial_vulkan_dep = vulkan_dep.partial_dependency(includes: true, sources: true, compile_args: true)
  dl_dep = meson.get_compiler('c').find_library('dl', disabler: true, required: get_option('examples'))
  if get_option('build_cpp').enabled()
    executable('cpp-basic-use', files('basic_use.cpp'), dependencies: [ vkfl_cpp_dep, vulkan_dep ])
    executable('cpp-global-use', files('global_use.cpp'), dependencies: [ vkfl_cpp_dep, partial_vulkan_dep, dl_dep ])
  endif
  if get_option('build_c').enabled()
    executable('c-basic-use', files('basic_use.c'), dependencies: [ vkfl_c_dep, vulkan_dep ])
    executable('c-global-use', files('global_use.c'), dependencies: [ vkfl_c_dep, partial_vulkan_dep, dl_dep ])
  endif
endif
