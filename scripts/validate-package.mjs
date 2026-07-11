import { readFile } from "node:fs/promises";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { parse } from "smol-toml";

const plugin = parse(await readFile("plugins/amazon-listing-optimizer/plugin.toml", "utf8"));
const marketplace = parse(await readFile("marketplace/yijie-marketplace.toml", "utf8"));
const registered = marketplace.plugins?.find((entry) => entry.id === plugin.id);
if (!registered || registered.version !== plugin.version || registered.risk_level !== plugin.risk_level) {
  throw new Error("Plugin metadata does not match the marketplace entry.");
}

const schema = JSON.parse(await readFile("shared/output-schemas/listing-diagnosis.schema.json", "utf8"));
const example = JSON.parse(
  await readFile("plugins/amazon-listing-optimizer/skills/listing-diagnosis/examples/output-001.json", "utf8"),
);
const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validate = ajv.compile(schema);
if (!validate(example)) throw new Error(`Invalid example output: ${ajv.errorsText(validate.errors)}`);

console.log("Validated plugin manifest, marketplace entry, schema, and example output.");
