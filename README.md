# vkfl

vkfl is a dynamic command function pointer loader for Vulkan. There are many other ways to load command function
pointers but I prefer this for the following reasons:

- vkfl doesn't introduce any global state.
- vkfl doesn't depend directly on Vulkan.
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

For examples of usage in source code see
[`examples/basic_use.cpp`](https://github.com/gn0mesort/vkfl/blob/master/examples/basic_use.cpp).

## Acknowledgements

Parts of `generate.py` are based on the equivalent file from [volk](https://github.com/zeux/volk). If you don't like
vkfl you should give volk a try instead.
