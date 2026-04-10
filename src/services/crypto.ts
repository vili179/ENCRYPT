export function xorCrypt(text: string, password: string): string {
  let keySum = 0;
  for (let i = 0; i < password.length; i++) {
    keySum += password.charCodeAt(i);
  }
  const key = keySum % 256;

  let result = "";
  for (let i = 0; i < text.length; i++) {
    result += String.fromCharCode(text.charCodeAt(i) ^ key);
  }
  return result;
}
