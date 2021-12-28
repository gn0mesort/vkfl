if true
  test_srcs = [ 'test_global.cpp' ]
  test_deps = [ vulkan_function_loader_dep, dependency('vulkan') ]
  test_exe = executable('global-function-load', test_srcs, dependencies: test_deps)
  test('global-function-load', test_exe)
endif
