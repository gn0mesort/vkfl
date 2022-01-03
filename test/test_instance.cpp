#include <cassert>
#include <cstring>

#include <vulkan/vulkan.h>

#include "vkfl.hpp"

#define VKFL_GET_PFN(ld, cmd) (reinterpret_cast<PFN_vk##cmd>(ld(vkfl::command::cmd)))

int main() {
  auto ld = vkfl::loader{ vkGetInstanceProcAddr };
  auto app_info = VkApplicationInfo{ };
  std::memset(&app_info, 0, sizeof(VkApplicationInfo));
  app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  {
#if defined(VKFL_USE_API_1_1)
    auto pfn = VKFL_GET_PFN(ld, EnumerateInstanceVersion);
    assert(pfn != nullptr);
    auto res = pfn(&app_info.apiVersion);
    assert(pfn(&app_info.apiVersion) == VK_SUCCESS);
    (void) res;
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
    auto pfn = VKFL_GET_PFN(ld, CreateInstance);
    assert(pfn != nullptr);
    auto res = pfn(&instance_info, nullptr, &instance);
    assert(res == VK_SUCCESS);
    (void) res;
  }
  ld.load(instance);
  assert(VKFL_GET_PFN(ld, GetDeviceProcAddr) != nullptr);
  assert(VKFL_GET_PFN(ld, GetDeviceQueue) != nullptr);
  return 0;
}
