export function definePcProfilePort(adapter) {
  if (
    !adapter ||
    typeof adapter.load !== "function" ||
    typeof adapter.save !== "function"
  ) {
    throw new Error("El adaptador debe implementar load() y save(profile).");
  }

  return adapter;
}
