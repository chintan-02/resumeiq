// Mirrors resumeiq_api.privacy. Contact details are always hidden on screen (ported from v0.9
// privacy_tools); privacy mode also hides the name on the first line and "City, Region" pairs.
const EMAIL = /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g;
const PHONE = /\+?\d[\d\s().-]{7,}\d/g;

export function maskContact(text: string): string {
  return text.replace(EMAIL, "[email hidden]").replace(PHONE, "[phone hidden]");
}

const REGIONS =
  "AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT|Alberta|British Columbia|Manitoba|New Brunswick|Newfoundland and Labrador|" +
  "Nova Scotia|Ontario|Prince Edward Island|Quebec|Saskatchewan|Yukon|" +
  "AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|" +
  "OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|Canada|USA|United States|India|UK|United Kingdom";
const LOCATION = new RegExp(`\\b[A-Z][a-zA-Z.'-]+(?:\\s[A-Z][a-zA-Z.'-]+)?,\\s?(?:${REGIONS})\\b`, "g");
const NAME = /^((?:[A-Z][a-zA-Z'-]+\s+){1,3}[A-Z][a-zA-Z'-]+)\b/;
const HEADING_WORDS = new Set([
  "summary", "experience", "education", "skills", "projects", "profile", "certifications", "contact", "objective", "resume",
]);

export function maskLocation(text: string): string {
  return text.replace(LOCATION, "[location hidden]");
}

/** Mask a name at the start of a line, used only on a document's first line. */
export function maskName(line: string): string {
  const name = line.match(NAME);
  if (!name || /\d|@/.test(name[1]) || name[1].toLowerCase().split(/\s+/).some((w) => HEADING_WORDS.has(w))) return line;
  return line.replace(name[1], "[name hidden]");
}

/** Text safe to show or export in privacy mode (contact details are always hidden). */
export function privateText(text: string, privacy: boolean): string {
  const masked = maskContact(text);
  return privacy ? maskLocation(masked) : masked;
}
