# VKFL

VKFL is a dynamic command function pointer loader and dispatch table for Vulkan.

While there are plenty of other ways to achieve this I prefer vkfl because:

- VKFL doesn't introduce any global state and namespaces all symbols.
- VKFL doesn't depend directly on libvulkan or the Vulkan headers.
- VKFL doesn't require any special compile time configuration of Vulkan.
- VKFL's generator can generate relatively small files (~55KiB for the header and ~25KiB for the source file) compared to other similar tools.
- VKFL's generator can generate files for specific API versions and extensions (e.g. Vulkan 1.3 with only `VK_KHR_surface`, `VK_KHR_xcb_surface`, and `VK_KHR_swapchain`).
- VKFL is easy to use as a [Meson](https://mesonbuild.com) subproject.

## Setup

Before VKFL can be generated you need to have [Mako](https://www.makotemplates.org/) and [`defusedxml`](https://pypi.org/project/defusedxml/) installed. You
can install these modules automatically with:

```sh
pip3 install -r requirements.txt
```

I recommend setting up and using a virtual environment prior to installing dependencies.

## Usage

Once dependencies are installed, the easiest way to include vkfl in a project is as a Meson subproject. This can be 
done by placing a copy of this repository under your `subprojects/` directory and adding the following to your build
file. If you're using C++ simply add the following to your `meson.build`:

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

vkfl can also be used by generating `vkfl.hpp` and `vkfl.cpp` directly to do this just build the meson project as
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

vkfl's generator can be found in [`tools/generate.py`](https://github.com/gn0mesort/vkfl/blob/master/tools/generate.py).
The usage is as follows:

```
usage: generate.py [-h] [--spec SPEC] [--extensions EXTENSIONS] [--api API] [--no-generate-disabled-defines] INPUT OUTPUT

positional arguments:
  INPUT                 A path to an input template file.
  OUTPUT                A path to an output file.

options:
  -h, --help            show this help message and exit
  --spec SPEC           A file path to an XML specification of the Vulkan API. If this isn't provided, the script will default to searching a set of standard paths for vk.xml.
  --extensions EXTENSIONS
                        A comma separated list of Vulkan extensions to include in the loader. This may also be the special value "all". Defaults to "all".
  --api API             The latest Vulkan API version to include in the loader (i.e., 1.0, 1.1, 1.2, etc.). This may also be the special value "latest". Defaults to "latest".
  --no-generate-disabled-defines
                        Disable the generation of symbols indicating that an extension or API version is disabled (i.e., don't generate VKFL_X_ENABLED if it would be defined as 0).

If a specification path is not explicitly provided, the following locations are searched.
Unix-like systems:
  $VULKAN_SDK/share/vulkan/registry/vk.xml
  $HOME/.local/share/vulkan/registry/vk.xml
  /usr/local/share/vulkan/registry/vk.xml
  /usr/share/vulkan/registry/vk.xml
Windows systems:
  %VULKAN_SDK%/share/vulkan/registry/vk.xml
  %VULKAN_SDK_PATH%/share/vulkan/registry/vk.xmlCD%/vk.xml
```

It's possible to use the generator with any input file. However, [`include/vkfl.hpp.in`](https://github.com/gn0mesort/vkfl/blob/master/include/vkfl.hpp.in) and
[`src/vkfl.cpp.in`](https://github.com/gn0mesort/vkfl/blob/master/src/vkfl.cpp.in) are intended to generate the canonical C++ implementation. Similarly,
[`include/vkfl.h.in`](https://github.com/gn0mesort/vkfl/blob/master/include/vkfl.h.in) and
[`src/vkfl.c.in`](https://github.com/gn0mesort/vkfl/blob/master/src/vkfl.c.in) should be used to generate the
canonical C implementation.

## C and C++ Implementations

vkfl provides both a C18 (i.e., C11) and a C++20 (although it will probably compile with previous standards too)
implementation. While these are largely the same they are not necessarily related. You probably shouldn't use
both implementations at the same time. In any case, `vkfl::loader` and `vkfl_loader` are not guaranteed to be binary
compatible. Don't assume you can safely `memcpy` between them even if it works.

By default both C and C++ implementations are built. To disable one or the other you can configure meson with
`-Dbuild_c=disabled` or `-Dbuild_cpp=disabled` respectively.

## Building Tests and Examples

By default test targets and example targets are disabled. To enable tests ensure that you have a build directory
configured and then run:

```sh
meson configure build -Dbuild_tests=enabled
```

To enable examples run:

```sh
meson configure build -Dbuild_examples=enabled
```

The `example/global_use.cpp` and `example/global_use.c` files require `dlfcn.h`, `dlopen`, `dlclose`, and `dlsym` to
compile (i.e., they won't compile on Windows).

## Building Documentation

HTML documentation requires [Doxygen](https://www.doxygen.nl/) and can be built with the following:

```sh
ninja -C build documentation
```

## Acknowledgements

In earlier versions of VKFL, parts of `generate.py` were based on the equivalent file from 
[volk](https://github.com/zeux/volk). If you don't like VKFL you should give volk a try instead. Much of the current
implementation was inspired by similar dispatch table generation scripts found in [Mesa](https://mesa3d.org/).
