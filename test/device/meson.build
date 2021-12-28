if true
  test_srcs = [ 'test_device.cpp' ]
  test_deps = [ vulkan_function_loader_dep, dependency('vulkan') ]
  test_exe = executable('device-function-load', test_srcs, dependencies: test_deps)
  test('device-function-load', test_exe)
endif
