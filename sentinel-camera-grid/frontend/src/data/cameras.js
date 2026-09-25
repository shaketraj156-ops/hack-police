// Camera city names — declared outside the array generator per guide §6
const cityNames = [
  "Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot",
  "Bhavnagar", "Jamnagar", "Junagadh", "Anand", "Bharuch"
];

export const cameras = Array.from({ length: 30 }, (_, index) => {
  const number = String(index + 1).padStart(2, "00");
  const providerId = `cam${number}`;
  return {
    providerId,
    displayName: `CAM-${number}`,
    location: cityNames[index % cityNames.length],
    // cam03 is intentionally OFFLINE to demonstrate the offline state
    status: providerId === "cam03" ? "OFFLINE" : "ONLINE",
    hlsUrl: `https://cctv.corp8.cloud/${providerId}/index.m3u8`
  };
});
