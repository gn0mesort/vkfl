#include <cassert>
#include <cstring>

#include <vulkan/vulkan.h>

#include "vkfl.hpp"

#define VKFL_GET_PFN(ld, cmd) (reinterpret_cast<vkfl::function_pointer::cmd>(ld(vkfl::command::cmd)))

int main() {
  auto ld = vkfl::loader{ vkGetInstanceProcAddr };
  auto app_info = VkApplicationInfo{ };
  std::memset(&app_info, 0, sizeof(VkApplicationInfo));
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  {
#if defined(VK_VERSION_1_1)
    auto pfn = VKFL_GET_PFN(ld, enumerate_instance_version);
    assert(pfn != nullptr);
    auto res = pfn(&app_info.apiVersion);
    assert(res == VK_SUCCESS);
#else
    app_info.apiVersion = VK_VERSION_1_0;
#endif
  }
  auto instance_info = VkInstanceCreateInfo{ };
  std::memset(&instance_info, 0, sizeof(VkInstanceCreateInfo));
  instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  instance_info.pApplicationInfo = &app_info;
  auto instance = VkInstance{ };
  {
    auto pfn = VKFL_GET_PFN(ld, create_instance);
    assert(pfn != nullptr);
    auto res = pfn(&instance_info, nullptr, &instance);
    assert(res == VK_SUCCESS);
  }
  ld.load(instance);
  assert(VKFL_GET_PFN(ld, get_device_proc_addr) != nullptr);
  assert(VKFL_GET_PFN(ld, get_device_queue) != nullptr);
  return 0;
}
