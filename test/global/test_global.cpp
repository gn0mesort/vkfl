#include <cassert>

#include <vulkan/vulkan.h>

#include "function_loader.hpp"

#define VK_GET_PFN(ld, cmd) (reinterpret_cast<vk::function_pointers::cmd>(ld(vk::command::cmd)))

int main() {
  auto ld = vk::function_loader{ vkGetInstanceProcAddr };
  assert(VK_GET_PFN(ld, create_instance) != nullptr);
  return 0;
}
