// Genererer én DeckSync-profil per enhetstype (zip med JSON, samme struktur som appens egne eksporter),
// med sidemarkør på hver side, Neste/Forrige side-knapper og sidehjul på dial 1 der enheten har dialer.
// Skriver også Profiles-blokken i manifestet, så manifest og filer alltid stemmer overens.
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { strToU8, zipSync } from "fflate";

const PLUGIN_DIR = "no.berland.decksync.sdPlugin";
const PLUGIN_UUID = "no.berland.decksync";
const MARKER_UUID = `${PLUGIN_UUID}.marker`;
const DIAL_UUID = `${PLUGIN_UUID}.dial`;
const NO_PAGE = "00000000-0000-0000-0000-000000000000";

/** Deterministisk UUID fra en streng, så bygget gir samme filer hver gang. */
const uuid = (seed) => {
	const h = createHash("sha1").update(seed).digest("hex");
	return `${h.slice(0, 8)}-${h.slice(8, 12)}-4${h.slice(13, 16)}-a${h.slice(17, 20)}-${h.slice(20, 32)}`;
};

const actionEntry = (uuidStr, name, plugin, settings, seed) => ({
	ActionID: uuid(seed),
	LinkedTitle: true,
	Name: name,
	Plugin: plugin,
	Resources: null,
	Settings: settings,
	State: 0,
	States: [{}],
	UUID: uuidStr,
});

export function generateProfiles() {
	const config = JSON.parse(readFileSync("decksync.config.json", "utf8"));
	const manifestPath = `${PLUGIN_DIR}/manifest.json`;
	const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
	const ownPlugin = { Name: manifest.Name, UUID: PLUGIN_UUID, Version: manifest.Version };
	const pagesPlugin = { Name: "Pages", UUID: "com.elgato.streamdeck.page", Version: "1.0" };

	mkdirSync(`${PLUGIN_DIR}/profiles`, { recursive: true });
	const profiles = [];

	for (const d of config.devices) {
		const profileId = uuid(`profile/${d.type}`);
		const pageIds = Array.from({ length: config.pages }, (_, i) => uuid(`page/${d.type}/${i + 1}`));
		const root = `Profiles/${profileId.toUpperCase()}.sdProfile`;
		const files = {};

		files[`${root}/manifest.json`] = strToU8(
			JSON.stringify({
				Device: { Model: d.model, UUID: "" },
				Name: d.name,
				Pages: { Current: NO_PAGE, Default: pageIds[0], Pages: pageIds },
				Version: "3.0",
			}),
		);

		pageIds.forEach((pageId, i) => {
			const page = i + 1;
			const bottom = d.rows - 1;
			const keys = {
				"0,0": actionEntry(MARKER_UUID, "Page marker", ownPlugin, { page, showLabel: true }, `marker/${d.type}/${page}`),
			};
			if (page > 1) {
				keys[`0,${bottom}`] = actionEntry("com.elgato.streamdeck.page.previous", "Previous Page", pagesPlugin, {}, `prev/${d.type}/${page}`);
			}
			if (page < config.pages) {
				keys[`${d.columns - 1},${bottom}`] = actionEntry("com.elgato.streamdeck.page.next", "Next Page", pagesPlugin, {}, `next/${d.type}/${page}`);
			}
			const controllers = [{ Actions: keys, Type: "Keypad" }];
			if (d.dials > 0) {
				controllers.push({ Actions: { "0,0": actionEntry(DIAL_UUID, "Page dial", ownPlugin, {}, `dial/${d.type}/${page}`) }, Type: "Encoder" });
			}
			files[`${root}/Profiles/${pageId.toUpperCase()}/manifest.json`] = strToU8(JSON.stringify({ Controllers: controllers, Icon: "", Name: "" }));
		});

		files["package.json"] = strToU8(
			JSON.stringify({ AppVersion: "7.5.1.22901", DeviceModel: d.model, DeviceSettings: null, FormatVersion: 1, OSType: "Windows", OSVersion: "10.0.26200", RequiredPlugins: [] }),
		);

		writeFileSync(`${PLUGIN_DIR}/profiles/${d.name}.streamDeckProfile`, zipSync(files, { level: 6 }));
		profiles.push({ Name: `profiles/${d.name}`, DeviceType: d.type, Readonly: false, DontAutoSwitchWhenInstalled: true, AutoInstall: true });
	}

	manifest.Profiles = profiles;
	writeFileSync(manifestPath, JSON.stringify(manifest, null, "\t") + "\n");
	console.log(`profiler: ${profiles.map((p) => p.Name).join(", ")} (${config.pages} sider hver)`);
}

if (process.argv[1] && process.argv[1].endsWith("gen-profiles.mjs")) generateProfiles();
