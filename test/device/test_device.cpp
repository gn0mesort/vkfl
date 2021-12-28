#include <cassert>
#include <cinttypes>
#include <cstring>

#include <vulkan/vulkan.h>

#include "function_loader.hpp"

#define VKFL_GET_PFN(ld, cmd) (reinterpret_cast<vkfl::function_pointer::cmd>(ld(vkfl::command::cmd)))

int main() {
  auto ld = vkfl::function_loader{ vkGetInstanceProcAddr };
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
  ld = vkfl::function_loader{ std::move(ld), instance };
  auto device_info = VkDeviceCreateInfo{ };
  std::memset(&device_info, 0, sizeof(VkDeviceCreateInfo));
  device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
  auto pdev = VkPhysicalDevice{ };
  {
    auto pfn = VKFL_GET_PFN(ld, enumerate_physical_devices);
    assert(pfn != nullptr);
    auto sz = std::uint32_t{ 1 };
    auto res = pfn(instance, &sz, &pdev);
    assert(res >= 0);
  }
  auto device = VkDevice{ };
  {
    auto pfn = VKFL_GET_PFN(ld, create_device);
    assert(pfn != nullptr);
    auto res = pfn(pdev, &device_info, nullptr, &device);
    assert(res == VK_SUCCESS);
  }
  auto old_pfn = VKFL_GET_PFN(ld, cmd_draw);
  ld = vkfl::function_loader{ std::move(ld), device };
  auto new_pfn = VKFL_GET_PFN(ld, cmd_draw);
  assert(new_pfn != nullptr);
  assert(new_pfn != old_pfn);
  return 0;
}
