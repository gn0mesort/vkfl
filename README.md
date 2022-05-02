# vkfl

vkfl is a dynamic command function pointer loader for Vulkan. There are many other ways to load command function
pointers but I prefer this for the following reasons:

- vkfl doesn't introduce any global state.
- vkfl doesn't depend directly on libvulkan or Vulkan headers.
- vkfl's generator can generate relatively small files (<100KiB total for Vulkan 1.3 with all extensions by default).
- vkfl's generator can generate files for specific API versions and extensions.
- vkfl is easy to use as a [Meson](https://mesonbuild.com) subproject.

I think this makes it easy to drop vkfl into a project without having to worry about whether or not it will cause a
conflict. 

## Using

The easiest way to include vkfl in a project is as a Meson subproject. This can be done by placing a copy of this
repository under your `subprojects/` directory and adding the following to your build file.
```meson
vkfl_proj = subproject('vkfl')
vkfl_dep = vkfl_proj.get_variable('vkfl_dep')
```
after that just include `vkfl_dep` as a dependency of your project.

vkfl can also be used by generating `vkfl.hpp` and `vkfl.cpp` to do this just build the meson project as follows:
```sh
meson build
ninja -C build
```
and then copy the resulting files (`build/vkfl.hpp` and `build/vkfl.cpp`) into your project.

Finally, you can generate `vkfl.hpp` and `vkfl.cpp` manually. To do this run `tools/generate.py` as follows:
```sh
mkdir -p build
tools/generate.py include/vkfl.hpp.in build/vkfl.hpp
tools/generate.py src/vkfl.cpp.in build/vkfl.cpp
```
and then copy the resulting files as above.

For examples of usage in source code see
[`examples`](https://github.com/gn0mesort/vkfl/blob/master/examples/).

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
It's possible to use the generator with any input file but [`include/vkfl.hpp.in`](https://github.com/gn0mesort/vkfl/blob/master/include/vkfl.hpp.in) and
[`src/vkfl.cpp.in`](https://github.com/gn0mesort/vkfl/blob/master/src/vkfl.cpp.in) are intended to generate the canonical implementation.

## Acknowledgements

Parts of `generate.py` are based on the equivalent file from [volk](https://github.com/zeux/volk). If you don't like
vkfl you should give volk a try instead.
