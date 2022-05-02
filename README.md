# vkfl

vkfl is a dynamic command function pointer loader and dispatch table for Vulkan.

While there are plenty of other ways to achieve this I prefer vkfl because:

- vkfl doesn't introduce any global state and namespaces all symbols.
- vkfl doesn't depend directly on libvulkan or Vulkan headers.
- vkfl doesn't require any special compile time configuration of Vulkan.
- vkfl's generator can generate relatively small files (~50KiB for the header and ~25KiB for the source file) compared to other similar tools.
- vkfl's generator can generate files for specific API versions and extensions (e.g. Vulkan 1.3 with only `VK_KHR_surface`, `VK_KHR_xcb_surface`, and `VK_KHR_swapchain`).
- vkfl is easy to use as a [Meson](https://mesonbuild.com) subproject.

## Usage

The easiest way to include vkfl in a project is as a Meson subproject. This can be done by placing a copy of this
repository under your `subprojects/` directory and adding the following to your build file. If you're using C++ simply
add the following to your `meson.build`:
```meson
vkfl_proj = subproject('vkfl')
vkfl_dep = vkfl_proj.get_variable('vkfl_cpp_dep')
```
If you'd like to use the C implementation instead add:
```meson
vkfl_proj = subproject('vkfl')
vkfl_dep = vkfl_proj.get_variable('vkfl_c_dep')
```
Afterward, just include `vkfl_dep` as a dependency of your project.

vkfl can also be used by generating directly `vkfl.hpp` and `vkfl.cpp` to do this just build the meson project as
follows:
```sh
meson build
ninja -C build
```
and then copy the resulting files (`build/vkfl.hpp` and `build/vkfl.cpp` for C++ or `build/vkfl.h` and
`build/vkfl.c` for C) into your project.

Finally, you can use the generator script manually. To do this run `tools/generate.py` as follows:
```sh
# Generates C++ files
mkdir -p build
tools/generate.py include/vkfl.hpp.in build/vkfl.hpp
tools/generate.py src/vkfl.cpp.in build/vkfl.cpp

# Generates C files
mkdir -p build
tools/generate.py include/vkfl.h.in build/vkfl.h
tools/generate.py src/vkfl.c.in build/vkfl.c
```
Then, simply copy the resulting files as above.

For examples of usage in source code see [`examples`](https://github.com/gn0mesort/vkfl/blob/master/examples/).

## Generator Usage

vkfl's generator can be found in [`tools/generate.py`](https://github.com/gn0mesort/blob/master/tools/generator.py).
The usage is as follows:
```
usage: generate.py [-h] [--spec SPEC] [--extensions EXTENSIONS] [--api API] [--generate-extra-defines] INPUT OUTPUT

positional arguments:
  INPUT                 A path to an input template file.
  OUTPUT                A path to an output file.

optional arguments:
  -h, --help            show this help message and exit
  --spec SPEC           Specifies the URI to load the XML Vulkan specification from. Defaults to "https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/xml/vk.xml".
  --extensions EXTENSIONS
                        A comma separated list of Vulkan extensions to include in the loader. This may also be the special value "all". Defaults to "all".
  --api API             The latest Vulkan API version to include in the loader (i.e. 1.0, 1.1, 1.2, etc.). This may also be the special value "latest". Defaults to "latest".
  --generate-extra-defines
                        Enable the generation of "VKFL_EXTORAPINAME_ENABLED" definitions with a value of 0 (disabled) as well as "VKFL_EXTNAME_EXTENSION_NAME" and "VKFL_EXTNAME_SPEC_VERSION" symbols. This is disabled by default.
```
It's possible to use the generator with any input file. However, [`include/vkfl.hpp.in`](https://github.com/gn0mesort/vkfl/blob/master/include/vkfl.hpp.in) and
[`src/vkfl.cpp.in`](https://github.com/gn0mesort/vkfl/blob/master/src/vkfl.cpp.in) are intended to generate the canonical C++ implementation. Similarly,
[`include/vkfl.h.in`](https://github.com/gn0mesort/vkfl/blob/master/include/vkfl.h.in) and
[`src/vkfl.c.in`](https://github.com/gn0mesort/vkfl/blob/master/src/vkfl.c.in) should be used to generate the
canonical C implementation.

## C and C++ Implementations

vkfl provides both a C18 (i.e. C11) and a C++20 (although it will probably compile with previous standards too)
implementation. While these are largely the same they are not necessarily related. You probably shouldn't use
both implementations at the same time. In any case, `vkfl::loader` and `vkfl_loader` are not guaranteed to be binary
compatible.

## Acknowledgements

Parts of `generate.py` are based on the equivalent file from [volk](https://github.com/zeux/volk). If you don't like
vkfl you should give volk a try instead.
