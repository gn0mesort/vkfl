#include <cassert>

#include <vulkan/vulkan.h>

#include "function_loader.hpp"

#define VKFL_GET_PFN(ld, cmd) (reinterpret_cast<vkfl::function_pointer::cmd>(ld(vkfl::command::cmd)))

int main() {
  auto ld = vkfl::function_loader{ vkGetInstanceProcAddr };
  assert(VKFL_GET_PFN(ld, create_instance) != nullptr);
  return 0;
}
