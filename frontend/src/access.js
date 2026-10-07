export function accessHeaders() {
  const token = sessionStorage.getItem('mahthildis-access-token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}
