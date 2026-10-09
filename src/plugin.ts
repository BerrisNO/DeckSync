import streamDeck, {
	action,
	SingletonAction,
	type Action,
	type DialAction,
	type DialDownEvent,
	type DialRotateEvent,
	type DialUpEvent,
	type Device,
	type DidReceiveSettingsEvent,
	type KeyDownEvent,
	type KeyUpEvent,
	type TouchTapEvent,
	type WillAppearEvent,
	type WillDisappearEvent,
} from "@elgato/streamdeck";
import { existsSync, readdirSync, readFileSync, statSync, watch } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import config from "../decksync.config.json";

/** Egen UUID (manifestet skal ikke leses ved kjøretid). */
const PLUGIN_UUID = "app.decksync";

type JsonObject = Parameters<typeof streamDeck.settings.setGlobalSettings>[0];
type JsonValue = JsonObject[string];
/** Det vi trenger av en enhet; SDK-ens hendelser gir Required<Device>, som ikke er tilordnbar til Device. */
type DeviceLike = Pick<Device, "id" | "name" | "type">;

/**
 * DeckSync – holder flere Stream Deck på samme side, eller sender hvert deck til sin side.
 *
 * Elgato-appen sender ingen "siden ble byttet"-event til plugins. Derfor ligger det en sidemarkør
 * på hver side i de genererte DeckSync-profilene. Når markøren dukker opp (willAppear), vet vi
 * hvilken side enheten står på, og sender de andre enhetene til tilsvarende side.
 *
 * I tillegg: «Gå til side» (side per enhet), «Sidehjul» (dial: vri = side, trykk = bytt mål)
 * og «Mål» (tast som bytter mellom ALLE og hvert deck).
 */

/** Antall sider i de genererte profilene. */
const PAGES: number = config.pages;

/** Profil per enhetstype. Generert av gen-profiles.mjs fra decksync.config.json. */
const PROFILE_BY_TYPE = new Map<number, string>(config.devices.map((d) => [d.type, `profiles/${d.name}`]));

/** Siste kjente side per enhet (1-basert). Beholdes når markøren forsvinner (mapper), fjernes ved frakobling. */
const currentPage = new Map<string, number>();
/** Sidebytter vi selv har bedt om, slik at vi ikke svarer på vårt eget ekko. */
const pendingEcho = new Map<string, { page: number; until: number }>();
/** Hvor lenge vi venter på ekkoet etter et sidebytte vi selv har sendt. */
const ECHO_WINDOW_MS = 2000;

const toInt = (v: unknown, fallback: number): number => {
	const n = typeof v === "number" ? v : parseInt(String(v ?? ""), 10);
	return Number.isFinite(n) && n >= 1 ? Math.floor(n) : fallback;
};

/** Tilkoblede enheter som har en DeckSync-profil. */
const syncable = (): Device[] => [...streamDeck.devices].filter((d) => d.isConnected && PROFILE_BY_TYPE.has(d.type));

/** Bytter én enhet til en side. Markøren som dukker opp etterpå er vårt eget ekko, ikke et brukerbytte. */
async function jumpTo(device: DeviceLike, page: number, why: string): Promise<void> {
	const profile = PROFILE_BY_TYPE.get(device.type);
	if (!profile) return;

	pendingEcho.set(device.id, { page, until: Date.now() + ECHO_WINDOW_MS });
	currentPage.set(device.id, page);
	streamDeck.logger.info(`DeckSync: ${why} → ${device.name} page ${page} (${profile})`);
	void refreshIndicators();

	try {
		await streamDeck.profiles.switchToProfile(device.id, profile, page - 1);
	} catch (err) {
		streamDeck.logger.error(`DeckSync: could not switch page on ${device.name}: ${err}`);
	}
}

// ---------------------------------------------------------------------------------------------
// Sidemarkør
// ---------------------------------------------------------------------------------------------

type MarkerSettings = {
	/** Hvilken side markøren står på (1 = første side). */
	page?: number | string;
	/** Valgfritt: hvilken side de andre enhetene skal til. Tomt = samme sidenummer. */
	target?: number | string;
	/** Vis sidenummer på knappen. */
	showLabel?: boolean;
};

async function syncFrom(sourceId: string, settings: MarkerSettings, force = false): Promise<void> {
	const page = toInt(settings.page, 1);
	const target = toInt(settings.target, page);

	for (const device of syncable()) {
		if (device.id === sourceId) continue;
		if (!force && currentPage.get(device.id) === target) continue;
		await jumpTo(device, target, `${sourceId} page ${page}`);
	}
}

const xmlEscape = (t: string): string => t.replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" })[c] ?? c);

// ---------------------------------------------------------------------------------------------
// Tastestil: samme flis som MA3Deck (mørk bakgrunn, avrundet flis med kant, nummer oppe til venstre,
// liten firkant oppe til høyre som lyser grønt når decket er i synk, navn i midten, notat nederst).
// ---------------------------------------------------------------------------------------------

const KEY_FONT = `font-family="Segoe UI, Arial, sans-serif"`;
const LIT = "#35D07F";
type Fit = { size: number; lines: string[] };

/** Bryter tekst til maks `maxLines` linjer med størst mulig skrift fra `sizes`. */
function fitText(text: string, width: number, sizes: number[], maxLines: number): Fit {
	const words = text.trim().split(/\s+/).filter(Boolean);
	for (const [i, size] of sizes.entries()) {
		const maxChars = Math.max(3, Math.floor(width / (size * 0.6)));
		const last = i === sizes.length - 1;
		const lines: string[] = [];
		let ok = true;
		for (let word of words) {
			if (word.length > maxChars) {
				if (!last) {
					ok = false;
					break;
				}
				word = `${word.slice(0, maxChars - 1)}…`;
			}
			const cur = lines[lines.length - 1];
			if (cur !== undefined && `${cur} ${word}`.length <= maxChars) lines[lines.length - 1] = `${cur} ${word}`;
			else lines.push(word);
		}
		if (ok && lines.length <= maxLines) return { size, lines };
		if (last) {
			const cut = lines.slice(0, maxLines);
			if (lines.length > maxLines) cut[maxLines - 1] = `${cut[maxLines - 1]!.slice(0, maxChars - 1)}…`;
			return { size, lines: cut };
		}
	}
	return { size: sizes[sizes.length - 1] ?? 16, lines: [] };
}

function textBlock(fit: Fit, centerY: number, fill: string, weight: number): string {
	const lineH = fit.size * 1.12;
	const top = centerY - (fit.lines.length * lineH) / 2 + fit.size * 0.85;
	return fit.lines
		.map((line, i) => `<text x="72" y="${(top + i * lineH).toFixed(1)}" font-size="${fit.size}" font-weight="${weight}" fill="${fill}" text-anchor="middle" ${KEY_FONT}>${xmlEscape(line)}</text>`)
		.join("");
}

type TileOptions = {
	/** Tekst oppe til venstre, f.eks. «p3». Gir også firkanten oppe til høyre. */
	number?: string;
	/** Liten tekst nederst i midten, f.eks. decknavn. */
	note?: string;
	/** Firkanten lyser grønt. */
	lit?: boolean;
	/** Nedtonet flis (ukjent side). */
	dim?: boolean;
	/** Sti til et ikon som tegnes over navnet (sideikonet fra appen). */
	icon?: string;
};

function tileSvg(text: string, { number = "", note = "", lit = false, dim = false, icon = "" }: TileOptions = {}): string {
	const fill = dim ? "#161C25" : "#232E3D";
	const textColor = dim ? "#3A4657" : "#FFFFFF";
	const hasNumber = number !== "";
	const hasNote = note !== "";
	const top0 = hasNumber ? 34 : 12;
	const bottom0 = hasNote ? 112 : 132;
	const iconSvg = icon && !dim ? iconMarkup(icon, 22, top0, 100, bottom0 - top0 - 26) : "";
	const hasImage = iconSvg !== "";
	const sizes = hasImage ? [20, 18, 16, 14] : hasNumber || hasNote ? [27, 24, 21, 18, 16] : [36, 31, 27, 23, 20];
	const label = fitText(text, 120, sizes, hasImage ? 1 : 2);
	const small = (x: number, y: number, anchor: string, value: string, opacity: number): string =>
		`<text x="${x}" y="${y}" font-size="16" font-weight="600" fill="${dim ? "#55637A" : textColor}" fill-opacity="${opacity}" text-anchor="${anchor}" ${KEY_FONT}>${xmlEscape(value)}</text>`;
	const labelY = hasImage ? bottom0 - 12 : (top0 + bottom0) / 2 + (hasNumber ? 2 : 0);
	// Med ikon (hvitt) over navnet får navnet en lys grå, så de to ikke flyter sammen.
	const labelColor = hasImage && !dim ? "#AEB9C7" : textColor;
	return (
		`<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">` +
		`<rect width="144" height="144" fill="#10151C"/>` +
		`<rect x="6" y="6" width="132" height="132" rx="14" fill="${fill}" stroke="${dim ? "#232E3D" : "#3A4657"}" stroke-width="3"/>` +
		iconSvg +
		textBlock(label, labelY, labelColor, 700) +
		(hasNumber ? small(16, 28, "start", number, dim ? 1 : 0.75) : "") +
		(hasNote ? small(72, 129, "middle", note, 0.6) : "") +
		(hasNumber ? `<rect x="113" y="14" width="17" height="17" rx="3" fill="${lit ? LIT : dim ? "#1B222C" : "#0E1319"}" stroke="${lit ? LIT : "#3A4657"}" stroke-width="1.5"/>` : "") +
		`</svg>`
	);
}

const svgUri = (svg: string): string => `data:image/svg+xml;base64,${Buffer.from(svg, "utf8").toString("base64")}`;

/** Står alle de andre deckene på samme side som dette? (minst ett annet deck må være kjent) */
function inSync(deviceId: string, page: number): boolean {
	const others = syncable().filter((d) => d.id !== deviceId);
	return others.length > 0 && others.every((d) => currentPage.get(d.id) === page);
}

async function showLabel(a: Action<MarkerSettings>, settings: MarkerSettings): Promise<void> {
	if (!a.isKey() && !a.isDial()) return;
	const page = toInt(settings.page, 1);
	const name = pageNameFor(page, a.device);
	try {
		if (a.isKey()) {
			await a.setTitle("");
			const show = settings.showLabel !== false;
			const svg = tileSvg(show && name ? name : "", {
				number: `Page ${page}`,
				lit: inSync(a.device.id, page),
				icon: pageIconFor(page, a.device) ?? DEFAULT_PAGE_ICON,
			});
			await a.setImage(svgUri(svg));
		} else {
			await a.setTitle(settings.showLabel === false ? "" : name ? `${name} · Page ${page}` : `Page ${page}`);
		}
	} catch {
		/* ignorer */
	}
}

@action({ UUID: "app.decksync.marker" })
class PageMarker extends SingletonAction<MarkerSettings> {
	override async onWillAppear(ev: WillAppearEvent<MarkerSettings>): Promise<void> {
		const settings = ev.payload.settings;
		await showLabel(ev.action, settings);

		const deviceId = ev.action.device.id;
		const page = toInt(settings.page, 1);

		// Er dette ekkoet av et bytte vi selv ba om? Da bare noterer vi siden.
		const echo = pendingEcho.get(deviceId);
		if (echo && Date.now() < echo.until) {
			pendingEcho.delete(deviceId);
			currentPage.set(deviceId, page);
			void refreshIndicators();
			return;
		}

		// Flere markører på samme side → bare den første teller.
		if (currentPage.get(deviceId) === page) return;

		currentPage.set(deviceId, page);
		await syncFrom(deviceId, settings);
		void refreshIndicators();
	}

	/**
	 * Markøren forsvinner også når decket går inn i en mappe på siden. Da husker vi siste kjente side,
	 * så stripen og synk-firkanten holder seg; en ny markør (annen side) eller frakobling erstatter den.
	 */
	override onWillDisappear(_ev: WillDisappearEvent<MarkerSettings>): void {
		/* beholder currentPage med vilje */
	}

	/** Trykk på markøren tvinger en ny synk (nyttig hvis noe har kommet i utakt). */
	override async onKeyDown(ev: KeyDownEvent<MarkerSettings>): Promise<void> {
		await syncFrom(ev.action.device.id, ev.payload.settings, true);
		if (ev.action.isKey()) await ev.action.showOk();
	}

	override async onDialDown(ev: DialDownEvent<MarkerSettings>): Promise<void> {
		await syncFrom(ev.action.device.id, ev.payload.settings, true);
	}

	override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<MarkerSettings>): Promise<void> {
		await showLabel(ev.action, ev.payload.settings);
		currentPage.set(ev.action.device.id, toInt(ev.payload.settings.page, 1));
	}
}

// ---------------------------------------------------------------------------------------------
// Gå til side
// ---------------------------------------------------------------------------------------------

/**
 * Innstillinger for «Go to page»: `all` = side for alle deck, ellers `page_<enhets-id>` per deck.
 * `sd15`/`plus` er de gamle feltene per enhetstype og virker fortsatt.
 */
type GotoSettings = { [key: string]: JsonValue };

const LEGACY_GOTO_KEY_BY_TYPE = new Map<number, string>([
	[0, "sd15"],
	[7, "plus"],
]);

/** Sender hvert deck til siden som er satt for det, også decket knappen ligger på. Tomt felt = decket røres ikke. */
async function gotoPages(settings: GotoSettings): Promise<void> {
	const all = toInt(settings.all, 0);
	for (const device of syncable()) {
		const legacy = LEGACY_GOTO_KEY_BY_TYPE.get(device.type);
		const page = all || toInt(settings[`page_${device.id}`], 0) || (legacy ? toInt(settings[legacy], 0) : 0);
		if (page < 1) continue;
		await jumpTo(device, page, "go to page");
	}
}

@action({ UUID: "app.decksync.goto" })
class GotoPage extends SingletonAction<GotoSettings> {
	override async onKeyDown(ev: KeyDownEvent<GotoSettings>): Promise<void> {
		await gotoPages(ev.payload.settings);
	}

	override async onDialDown(ev: DialDownEvent<GotoSettings>): Promise<void> {
		await gotoPages(ev.payload.settings);
	}

	override async onTouchTap(ev: TouchTapEvent<GotoSettings>): Promise<void> {
		await gotoPages(ev.payload.settings);
	}
}

// ---------------------------------------------------------------------------------------------
// Page step: neste/forrige side på en vanlig tast, for deck uten dial. Tasten viser siden den går til.
// ---------------------------------------------------------------------------------------------

type StepSettings = {
	/** "next" (standard), "prev", eller "both" = kort trykk neste, hold forrige. */
	mode?: string;
	/** "all" (standard) = alle deck, "this" = bare dette decket, "target" = det Target-tasten står på. */
	scope?: string;
};

/**
 * Decket en tast regner ut fra. Ligger tasten på et DeckSync-deck, er det decket selv. Ligger den på et deck
 * uten DeckSync-profil (f.eks. Virtual Stream Deck brukt som fjernkontroll), brukes målet, ellers første deck med kjent side.
 */
function referenceDevice(deviceId: string): Device | undefined {
	const decks = syncable();
	const own = decks.find((d) => d.id === deviceId);
	if (own) return own;
	const chosen = target === "all" ? undefined : decks.find((d) => d.id === target);
	return chosen ?? decks.find((d) => currentPage.has(d.id)) ?? decks[0];
}

/** Siden et steg går til, regnet fra referansedecket, eller undefined ved kanten / ukjent side. */
function stepDestination(deviceId: string, dir: number): number | undefined {
	const ref = referenceDevice(deviceId);
	const from = ref ? currentPage.get(ref.id) : undefined;
	if (!from) return undefined;
	const to = from + dir;
	return to >= 1 && to <= PAGES ? to : undefined;
}

async function renderStep(a: Action<StepSettings>, settings: StepSettings): Promise<void> {
	if (!a.isKey()) return;
	const dir = settings.mode === "prev" ? -1 : 1;
	const to = stepDestination(a.device.id, dir);
	const note = settings.mode === "prev" ? "\u2039 prev" : settings.mode === "both" ? "next \u203a" : "next \u203a";
	try {
		await a.setTitle("");
		const ref = referenceDevice(a.device.id);
		const svg = to && ref
			? tileSvg(pageNameFor(to, ref) ?? `Page ${to}`, { number: `Page ${to}`, note, icon: pageIconFor(to, ref) ?? DEFAULT_PAGE_ICON })
			: tileSvg("\u2014", { note, dim: true });
		await a.setImage(svgUri(svg));
	} catch {
		/* ignorer */
	}
}

async function doStep(a: Action<StepSettings>, settings: StepSettings, dir: number): Promise<void> {
	const own = syncable().find((d) => d.id === a.device.id);
	const to = stepDestination(a.device.id, dir);
	if (!to) {
		if (a.isKey()) await a.showAlert();
		return;
	}
	const scope = settings.scope ?? "all";
	// «This deck» på et deck uten DeckSync-profil (fjernkontroll) betyr alle deck.
	const devices = scope === "this" && own ? [own] : scope === "target" ? targetDevices() : syncable();
	for (const d of devices) await jumpTo(d, to, `page step (${scope})`);
}

const STEP_HOLD_MS = 500;
const stepDownAt = new Map<string, number>();

@action({ UUID: "app.decksync.step" })
class PageStep extends SingletonAction<StepSettings> {
	override async onWillAppear(ev: WillAppearEvent<StepSettings>): Promise<void> {
		await renderStep(ev.action, ev.payload.settings);
	}

	override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<StepSettings>): Promise<void> {
		await renderStep(ev.action, ev.payload.settings);
	}

	override async onKeyDown(ev: KeyDownEvent<StepSettings>): Promise<void> {
		const mode = ev.payload.settings.mode;
		if (mode === "both") {
			stepDownAt.set(ev.action.id, Date.now());
			return;
		}
		await doStep(ev.action, ev.payload.settings, mode === "prev" ? -1 : 1);
	}

	override async onKeyUp(ev: KeyUpEvent<StepSettings>): Promise<void> {
		if (ev.payload.settings.mode !== "both") return;
		const down = stepDownAt.get(ev.action.id) ?? Date.now();
		stepDownAt.delete(ev.action.id);
		await doStep(ev.action, ev.payload.settings, Date.now() - down >= STEP_HOLD_MS ? -1 : 1);
	}
}

// ---------------------------------------------------------------------------------------------
// Page indicator: viser siden et deck står på, i samme stil som markøren. Plasseres fritt.
// ---------------------------------------------------------------------------------------------

type IndicatorSettings = {
	/** Enhets-id for decket som vises. Tomt = decket tasten ligger på. */
	deck?: string;
};

/** Hvilket deck en indikator viser: valgt deck hvis det er tilkoblet, ellers eget deck. */
function indicatorDevice(a: Action<IndicatorSettings>, settings: IndicatorSettings): Device | undefined {
	const chosen = settings.deck ? streamDeck.devices.getDeviceById(settings.deck) : undefined;
	return chosen && chosen.isConnected ? chosen : referenceDevice(a.device.id);
}

async function renderIndicator(a: Action<IndicatorSettings>, settings: IndicatorSettings): Promise<void> {
	if (!a.isKey()) return;
	const shown = indicatorDevice(a, settings);
	const page = shown ? currentPage.get(shown.id) : undefined;
	const name = shown && page ? pageNameFor(page, shown) : undefined;
	const other = !!shown && shown.id !== a.device.id;
	const lit = !!shown && !!page && (other && currentPage.has(a.device.id) ? currentPage.get(a.device.id) === page : inSync(shown.id, page));
	try {
		await a.setTitle("");
		const svg = tileSvg(page ? (name ?? "") : "—", {
			number: page ? `Page ${page}` : "",
			note: other ? nameFor(shown) : "",
			lit,
			dim: !page,
			icon: shown && page ? (pageIconFor(page, shown) ?? DEFAULT_PAGE_ICON) : undefined,
		});
		await a.setImage(svgUri(svg));
	} catch {
		/* ignorer */
	}
}

/** Oppdaterer alle synlige markører og indikatorer (kalles når en side endrer seg, så synk-firkanten stemmer). */
async function refreshIndicators(): Promise<void> {
	for (const a of pageMarker.actions) {
		try {
			await showLabel(a, await a.getSettings());
		} catch {
			/* ignorer */
		}
	}
	for (const a of pageIndicator.actions) {
		try {
			await renderIndicator(a, await a.getSettings());
		} catch {
			/* ignorer */
		}
	}
	for (const a of pageStep.actions) {
		try {
			await renderStep(a, await a.getSettings());
		} catch {
			/* ignorer */
		}
	}
	for (const a of pageDial.actions) if (a.isDial()) await refreshDial(a);
}

@action({ UUID: "app.decksync.indicator" })
class PageIndicator extends SingletonAction<IndicatorSettings> {
	override async onWillAppear(ev: WillAppearEvent<IndicatorSettings>): Promise<void> {
		await renderIndicator(ev.action, ev.payload.settings);
	}

	override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<IndicatorSettings>): Promise<void> {
		await renderIndicator(ev.action, ev.payload.settings);
	}

	/** Trykk: viser den et annet deck, går dette decket til samme side. Viser den eget deck, tvinges en resynk. */
	override async onKeyDown(ev: KeyDownEvent<IndicatorSettings>): Promise<void> {
		const shown = indicatorDevice(ev.action, ev.payload.settings);
		if (!shown) return;
		const page = currentPage.get(shown.id);
		if (!page) return;
		const own = syncable().find((d) => d.id === ev.action.device.id);
		if (own && shown.id !== own.id) {
			await jumpTo(own, page, `indicator (${nameFor(shown)})`);
		} else {
			// eget deck, eller tast på et deck uten DeckSync-profil: alle andre til den viste siden
			await syncFrom(shown.id, { page }, true);
		}
		if (ev.action.isKey()) await ev.action.showOk();
	}
}

// ---------------------------------------------------------------------------------------------
// Sidehjul og Mål (deler mål og valgt side, lagret i globale innstillinger)
// ---------------------------------------------------------------------------------------------

type GlobalSettings = {
	/** "all" eller enhets-id. */
	target?: string;
	/** Siden sidehjulet står på. */
	dialPage?: number;
	/** Enheter der DeckSync-profilen er installert (markøren meldte seg etter førstegangsbyttet). */
	installedDevices?: string[];
	/** Tilkoblede deck (med type og profil), så innstillingssidene kan vise navnefelt og sidelister per deck. */
	devices?: { id: string; name: string; type: number; profile: string }[];
	/** Antall sider i profilene, så innstillingssidene kan lage lister. */
	pages?: number;
	/** Sidenavn per DeckSync-profil, lest fra appen, så «Go to page» kan vise navn. */
	pageNames?: Record<string, string[]>;
	/** Egendefinerte navn skrives av innstillingssiden som `deckname_<enhets-id>`. */
	[key: string]: JsonValue;
};

let target = "all";
let dialPage = 1;
let installed: string[] = [];
/** Alt annet i globale innstillinger (deck-navn fra innstillingssiden), så vi ikke sletter det når vi lagrer. */
let extraGlobals: Record<string, JsonValue> = {};

function applyGlobals(g: GlobalSettings): void {
	const { target: t, dialPage: p, installedDevices, devices: _devices, pages: _pages, pageNames: _pageNames, ...rest } = g;
	target = typeof t === "string" ? t : "all";
	dialPage = toInt(p, 1);
	installed = Array.isArray(installedDevices) ? installedDevices : [];
	extraGlobals = rest;
}

const saveGlobals = (): Promise<void> =>
	streamDeck.settings.setGlobalSettings<GlobalSettings>({
		...extraGlobals,
		target,
		dialPage,
		installedDevices: installed,
		devices: syncable().map((d) => ({ id: d.id, name: d.name, type: d.type, profile: PROFILE_BY_TYPE.get(d.type) ?? "" })),
		pages: PAGES,
		pageNames: pageNamesByProfile,
	});

/** "Stream Deck +" → "+", "Stream Deck Module 15" → "Module 15". */
const shortName = (d: DeviceLike): string => d.name.replace(/^Stream Deck\s*/i, "").trim() || d.name;

// ---------------------------------------------------------------------------------------------
// Sidenavn leses fra de installerte DeckSync-profilene i Stream Deck-appen (sidene navngis der).
// ---------------------------------------------------------------------------------------------

function profilesDir(): string | undefined {
	if (process.platform === "win32") return process.env.APPDATA ? join(process.env.APPDATA, "Elgato", "StreamDeck", "ProfilesV3") : undefined;
	if (process.platform === "darwin") return join(homedir(), "Library", "Application Support", "com.elgato.StreamDeck", "ProfilesV3");
	return undefined;
}

/** Sidenavn per profil (nøkkel = PreconfiguredName, f.eks. "profiles/DeckSync 15"), indeks 0 = side 1. */
let pageNamesByProfile: Record<string, string[]> = {};
/** Absolutt sti til sideikonet (satt i appen) per profil og side, tom streng = ingen. */
let pageIconsByProfile: Record<string, string[]> = {};

function scanPageNames(): void {
	const dir = profilesDir();
	if (!dir || !existsSync(dir)) return;
	const result: Record<string, string[]> = {};
	const icons: Record<string, string[]> = {};
	for (const entry of readdirSync(dir)) {
		if (!entry.endsWith(".sdProfile")) continue;
		try {
			const m = JSON.parse(readFileSync(join(dir, entry, "manifest.json"), "utf8"));
			if (m.InstalledByPluginUUID !== PLUGIN_UUID || typeof m.PreconfiguredName !== "string") continue;
			const ids: unknown = m.Pages?.Pages;
			if (!Array.isArray(ids)) continue;
			const names: string[] = [];
			const iconPaths: string[] = [];
			for (const id of ids) {
				const pageDir = join(dir, entry, "Profiles", String(id).toUpperCase());
				try {
					const pm = JSON.parse(readFileSync(join(pageDir, "manifest.json"), "utf8"));
					names.push(typeof pm.Name === "string" ? pm.Name.trim() : "");
					// Ikonstien er relativ til sidens mappe, f.eks. "Images/K4HB….svg"
					iconPaths.push(typeof pm.Icon === "string" && pm.Icon ? join(pageDir, pm.Icon) : "");
				} catch {
					names.push("");
					iconPaths.push("");
				}
			}
			result[m.PreconfiguredName] = names;
			icons[m.PreconfiguredName] = iconPaths;
		} catch {
			/* ikke en profil vi forstår */
		}
	}
	pageIconsByProfile = icons;
	const summary = JSON.stringify(result);
	if (summary !== lastPageNamesSummary) {
		lastPageNamesSummary = summary;
		streamDeck.logger.info(`DeckSync: page names from Stream Deck profiles: ${summary}`);
	}
	pageNamesByProfile = result;
}
let lastPageNamesSummary = "";

/** Følger med på profilmappen og leser sidenavn på nytt når noe endres (med liten forsinkelse). */
function watchPageNames(onChange: () => void): void {
	const dir = profilesDir();
	if (!dir || !existsSync(dir)) return;
	let timer: ReturnType<typeof setTimeout> | undefined;
	try {
		const watcher = watch(dir, { recursive: true }, () => {
			clearTimeout(timer);
			timer = setTimeout(() => {
				scanPageNames();
				onChange();
			}, 600);
		});
		watcher.unref(); // skal ikke holde prosessen i live alene
	} catch (err) {
		streamDeck.logger.warn(`DeckSync: could not watch profiles folder: ${err}`);
	}
}

/** Sidenavn for én enhet (fra dens DeckSync-profil), ellers undefined. */
function pageNameFor(page: number, device: Pick<Device, "type">): string | undefined {
	const profile = PROFILE_BY_TYPE.get(device.type);
	const name = profile ? pageNamesByProfile[profile]?.[page - 1] : undefined;
	return name ? name : undefined;
}

/** Sti til sideikonet (fra appen) for én enhet, ellers undefined. */
function pageIconFor(page: number, device: Pick<Device, "type">): string | undefined {
	const profile = PROFILE_BY_TYPE.get(device.type);
	const path = profile ? pageIconsByProfile[profile]?.[page - 1] : undefined;
	return path ? path : undefined;
}

const iconCache = new Map<string, { mtimeMs: number; markup: (x: number, y: number, w: number, h: number) => string }>();

/** Brukes som ikonsti når siden ikke har eget ikon i appen: et lite tastenett (en Stream Deck-side) i samme hvite strek som appens egne. */
const DEFAULT_PAGE_ICON = "default:page";
const DEFAULT_PAGE_ICON_INNER =
	`<rect x="2.3" y="5.6" width="5.4" height="5.4" rx="1.3" fill="none" stroke="white" stroke-width="1.5"/><rect x="9.3" y="5.6" width="5.4" height="5.4" rx="1.3" fill="none" stroke="white" stroke-width="1.5"/><rect x="16.3" y="5.6" width="5.4" height="5.4" rx="1.3" fill="none" stroke="white" stroke-width="1.5"/><rect x="2.3" y="13" width="5.4" height="5.4" rx="1.3" fill="none" stroke="white" stroke-width="1.5"/><rect x="9.3" y="13" width="5.4" height="5.4" rx="1.3" fill="none" stroke="white" stroke-width="1.5"/><rect x="16.3" y="13" width="5.4" height="5.4" rx="1.3" fill="none" stroke="white" stroke-width="1.5"/>`;

/** Skalerer og sentrerer SVG-innhold med gitt viewBox i en boks (appens tegner ignorerer nestede <svg>). */
function fitGroup(inner: string, vx: number, vy: number, vw: number, vh: number, bx: number, by: number, bw: number, bh: number): string {
	const sc = Math.min(bw / (vw || 1), bh / (vh || 1));
	const tx = bx + (bw - vw * sc) / 2 - vx * sc;
	const ty = by + (bh - vh * sc) / 2 - vy * sc;
	return `<g transform="translate(${tx.toFixed(2)} ${ty.toFixed(2)}) scale(${sc.toFixed(4)})">${inner}</g>`;
}

/**
 * SVG-markup for et sideikon plassert i en boks. SVG-ikoner limes inn som nestet <svg> (appens renderer
 * takler ikke alltid SVG via data-URI), bilder som <image> med base64. Tom streng hvis fila ikke kan leses.
 */
function iconMarkup(path: string, x: number, y: number, w: number, h: number): string {
	if (path === DEFAULT_PAGE_ICON) return fitGroup(DEFAULT_PAGE_ICON_INNER, 0, 0, 24, 24, x, y, w, h);
	try {
		const mtimeMs = statSync(path).mtimeMs;
		let entry = iconCache.get(path);
		if (!entry || entry.mtimeMs !== mtimeMs) {
			const ext = path.toLowerCase().split(".").pop() ?? "";
			if (ext === "svg") {
				const src = readFileSync(path, "utf8");
				const m = /<svg\b([^>]*)>([\s\S]*)<\/svg>/i.exec(src);
				if (!m) return "";
				const attrs = m[1] ?? "";
				const inner = m[2] ?? "";
				const vb = /viewBox\s*=\s*"([^"]+)"/i.exec(attrs)?.[1];
				const wAttr = /\bwidth\s*=\s*"([\d.]+)/i.exec(attrs)?.[1];
				const hAttr = /\bheight\s*=\s*"([\d.]+)/i.exec(attrs)?.[1];
				const viewBox = vb ?? (wAttr && hAttr ? `0 0 ${wAttr} ${hAttr}` : "0 0 24 24");
				const [vx = 0, vy = 0, vw = 24, vh = 24] = viewBox.trim().split(/[\s,]+/).map(Number);
				entry = { mtimeMs, markup: (bx, by, bw, bh) => fitGroup(inner, vx, vy, vw, vh, bx, by, bw, bh) };
			} else {
				const mime = ext === "png" ? "image/png" : ext === "jpg" || ext === "jpeg" ? "image/jpeg" : ext === "gif" ? "image/gif" : "";
				if (!mime) return "";
				const data = `data:${mime};base64,${readFileSync(path).toString("base64")}`;
				entry = { mtimeMs, markup: (bx, by, bw, bh) => `<image x="${bx}" y="${by}" width="${bw}" height="${bh}" preserveAspectRatio="xMidYMid meet" href="${data}"/>` };
			}
			iconCache.set(path, entry);
		}
		return entry.markup(x, y, w, h);
	} catch {
		return "";
	}
}

/** Sidenavn for ALLE: navnet når deckene er enige (tomme teller ikke), ellers undefined. */
function pageNameAll(page: number): string | undefined {
	const names = new Set(syncable().map((d) => pageNameFor(page, d)).filter((n): n is string => !!n));
	return names.size === 1 ? [...names][0] : undefined;
}

/** Egendefinert navn fra innstillingene, ellers enhetens korte navn. */
function nameFor(d: DeviceLike): string {
	const custom = extraGlobals[`deckname_${d.id}`];
	return typeof custom === "string" && custom.trim() ? custom.trim() : shortName(d);
}

function targetLabel(): string {
	if (target === "all") return "ALL";
	const d = streamDeck.devices.getDeviceById(target);
	return d ? nameFor(d) : "ALL";
}

function targetDevices(): Device[] {
	return target === "all" ? syncable() : syncable().filter((d) => d.id === target);
}

/** ALLE → deck 1 → deck 2 → … → ALLE (step = -1 går motsatt vei). */
function cycleTarget(step = 1): void {
	const ids = ["all", ...syncable().map((d) => d.id)];
	const i = Math.max(0, ids.indexOf(target));
	target = ids[(((i + step) % ids.length) + ids.length) % ids.length] ?? "all";
}

let sendTimer: ReturnType<typeof setTimeout> | undefined;

/** Sender målenhetene til sidehjulets side, med liten forsinkelse så rask vridning ikke gir ett bytte per hakk. */
function sendDialPage(delayMs: number): void {
	clearTimeout(sendTimer);
	sendTimer = setTimeout(() => {
		for (const d of targetDevices()) void jumpTo(d, dialPage, `page dial (${targetLabel()})`);
	}, delayMs);
}

/** Decknavn på stripen: egendefinert navn hvis satt, ellers Deck1, Deck2, … i tilkoblingsrekkefølge. */
function deckTag(d: DeviceLike, index: number): string {
	const custom = extraGlobals[`deckname_${d.id}`];
	return typeof custom === "string" && custom.trim() ? custom.trim() : `Deck${index + 1}`;
}

/** Én tekstrad på stripen (layouts/dial.json: badge + overskrift r1, cyan linje, rader r2–r4; størrelse/farge settes her). */
type StripRow = { value: string; font: { size: number; weight: number }; color: string; alignment: "left" | "right" };
const row = (value: string, size: number, color = "#ffffff", weight = 400, alignment: "left" | "right" = "left"): StripRow => ({ value, font: { size, weight }, color, alignment });
const EMPTY_ROW = row("", 14);
const DIM = "#7f8da0";
const GREY = "#9fb3c8";
const CYAN = "#26b8a8";
type StripFeedback = { r1: StripRow; r2: StripRow; r3: StripRow; r4: StripRow };
const emptyStrip = (): StripFeedback => ({ r1: EMPTY_ROW, r2: EMPTY_ROW, r3: EMPTY_ROW, r4: EMPTY_ROW });

/** «Deck1: P3 MA3 PROG» */
function deckLine(d: DeviceLike, index: number, page: number | undefined): string {
	const title = page ? pageNameFor(page, d) : undefined;
	return `${deckTag(d, index)}: ${page ? `Page ${page}` : "–"}${title ? ` ${title}` : ""}`;
}

/** Status: overskrift i cyan (ALL: P3, eller PAGES når deckene står ulikt) og én rad per deck under linjen. */
function statusFeedback(): StripFeedback {
	const out = emptyStrip();
	const decks = syncable();
	if (decks.length === 0) {
		out.r1 = row("No decks", 20, GREY, 700);
		return out;
	}
	const pages = decks.map((d) => currentPage.get(d.id));
	const first = pages[0];
	const inSyncAll = decks.length > 1 && !!first && pages.every((p) => p === first);
	let lines: string[];
	if (inSyncAll) {
		out.r1 = row(`ALL: Page ${first}`, 20, CYAN, 700);
		lines = decks.map((d, i) => {
			const title = pageNameFor(first, d);
			return title ? `${deckTag(d, i)} - ${title}` : deckTag(d, i);
		});
	} else if (decks.length === 1) {
		out.r1 = row(`Page ${first ?? "–"}`, 20, CYAN, 700);
		const title = first ? pageNameFor(first, decks[0]!) : undefined;
		lines = [title ? `${deckTag(decks[0]!, 0)} - ${title}` : deckTag(decks[0]!, 0)];
	} else {
		out.r1 = row("PAGES", 20, GREY, 700);
		lines = decks.map((d, i) => deckLine(d, i, pages[i]));
	}
	const size = lines.length <= 2 ? 15 : 13;
	if (lines.length <= 3) {
		[out.r2, out.r3, out.r4] = [0, 1, 2].map((i) => (lines[i] ? row(lines[i]!, size) : EMPTY_ROW)) as [StripRow, StripRow, StripRow];
	} else {
		out.r2 = row(lines[0]!, size);
		out.r3 = row(lines[1]!, size);
		out.r4 = row(`+${lines.length - 2} more`, size, DIM);
	}
	return out;
}

/** Valget mens man vrir/holder: «→ P4» i cyan som overskrift, tittel og mål under. */
function selectionFeedback(): StripFeedback {
	const out = emptyStrip();
	if (holding) {
		out.r1 = row("TURN: DECK", 20, CYAN, 700);
		out.r2 = row(`target: ${targetLabel()}`, 15);
		return out;
	}
	const targetDevice = target === "all" ? undefined : streamDeck.devices.getDeviceById(target);
	const name = targetDevice ? pageNameFor(dialPage, targetDevice) : pageNameAll(dialPage);
	out.r1 = row(`→ Page ${dialPage}`, 20, CYAN, 700);
	out.r2 = row(name ?? "", 15);
	out.r3 = row(`target: ${targetLabel()}`, 13, GREY);
	return out;
}

/** Hvor lenge valget vises på stripen etter siste vridning/trykk, før status kommer tilbake. */
const SELECTION_SHOW_MS = 2500;
let selectionUntil = 0;
let selectionTimer: ReturnType<typeof setTimeout> | undefined;

/** Kalles ved vridning/trykk: vis valget en stund, så status igjen. */
function showSelection(): void {
	selectionUntil = Date.now() + SELECTION_SHOW_MS;
	clearTimeout(selectionTimer);
	selectionTimer = setTimeout(() => {
		selectionUntil = 0;
		for (const a of pageDial.actions) if (a.isDial()) void refreshDial(a);
	}, SELECTION_SHOW_MS + 50);
}

async function refreshDial(a: DialAction<JsonObject>): Promise<void> {
	try {
		await a.setFeedback(holding || Date.now() < selectionUntil ? selectionFeedback() : statusFeedback());
	} catch {
		/* ignorer */
	}
}

/** Oppdaterer alle synlige sidehjul, mål-taster, markørtitler og indikatorer. */
async function refreshAll(): Promise<void> {
	await refreshIndicators();
	for (const a of targetKey.actions) if (a.isKey()) await renderTargetKey(a);
}

/** Mål-tasten: målet stort, «target» som notat nederst. */
async function renderTargetKey(a: Action<JsonObject>): Promise<void> {
	if (!a.isKey()) return;
	try {
		await a.setTitle("");
		await a.setImage(svgUri(tileSvg(targetLabel(), { note: "target" })));
	} catch {
		/* ignorer */
	}
}

/** Så lenge må dialen holdes før et slipp ikke lenger teller som «gå til side». */
const HOLD_MS = 500;
let holdTimer: ReturnType<typeof setTimeout> | undefined;
/** Dialen holdes inne (viser hint på stripen). */
let holding = false;
/** Trykket har vart lenge, eller dialen ble vridd mens den var inne: slipp skal ikke sende. */
let holdConsumed = false;

/**
 * Sidehjul: vri = velg side (sender ikke), kort trykk = gå til siden,
 * hold + vri = velg mål (ALL → deck 1 → deck 2 → …, begge veier). Hold alene gjør ingenting. Touch-feltet sender.
 */
@action({ UUID: "app.decksync.dial" })
class PageDial extends SingletonAction {
	override async onWillAppear(ev: WillAppearEvent): Promise<void> {
		if (ev.action.isDial()) await refreshDial(ev.action);
	}

	override async onDialRotate(ev: DialRotateEvent): Promise<void> {
		const ticks = ev.payload.ticks;
		if (ev.payload.pressed || holding) {
			holdConsumed = true;
			clearTimeout(holdTimer);
			for (let i = 0; i < Math.abs(ticks); i++) cycleTarget(Math.sign(ticks));
		} else {
			dialPage = Math.min(PAGES, Math.max(1, dialPage + ticks));
		}
		showSelection();
		await refreshAll();
		void saveGlobals();
	}

	override async onDialDown(_ev: DialDownEvent): Promise<void> {
		holding = true;
		holdConsumed = false;
		clearTimeout(holdTimer);
		holdTimer = setTimeout(() => {
			holdConsumed = true;
			void refreshAll(); // viser «turn: deck» på stripen
		}, HOLD_MS);
	}

	override async onDialUp(_ev: DialUpEvent): Promise<void> {
		clearTimeout(holdTimer);
		holdTimer = undefined;
		holding = false;
		if (!holdConsumed) sendDialPage(0);
		showSelection();
		await refreshAll();
	}

	override async onTouchTap(): Promise<void> {
		sendDialPage(0);
	}
}

@action({ UUID: "app.decksync.target" })
class TargetKey extends SingletonAction {
	override async onWillAppear(ev: WillAppearEvent): Promise<void> {
		await renderTargetKey(ev.action);
	}

	override async onKeyDown(): Promise<void> {
		cycleTarget();
		await refreshAll();
		void saveGlobals();
	}
}

const pageMarker = new PageMarker();
const pageStep = new PageStep();
const pageIndicator = new PageIndicator();
const pageDial = new PageDial();
const targetKey = new TargetKey();

// ---------------------------------------------------------------------------------------------
// Oppstart
// ---------------------------------------------------------------------------------------------

streamDeck.actions.registerAction(pageMarker);
streamDeck.actions.registerAction(new GotoPage());
streamDeck.actions.registerAction(pageIndicator);
streamDeck.actions.registerAction(pageStep);
streamDeck.actions.registerAction(pageDial);
streamDeck.actions.registerAction(targetKey);

/** Globale innstillinger må være lest før vi avgjør om en enhet trenger førstegangsinstallasjon. */
const globalsLoaded = streamDeck
	.connect()
	.then(() => streamDeck.settings.getGlobalSettings<GlobalSettings>())
	.then((g) => applyGlobals(g))
	.catch((err) => streamDeck.logger.error(`DeckSync: could not read global settings: ${err}`));

/** Innstillingssiden lagrer deck-navn globalt; da oppdaterer vi teksten på sidehjul og mål-taster. */
streamDeck.settings.onDidReceiveGlobalSettings<GlobalSettings>((ev) => {
	applyGlobals(ev.settings);
	void refreshAll();
});

/**
 * Førstegangsinstallasjon må gå én enhet om gangen: appen avviser en profilimport mens en annen pågår
 * ("Another operation is already in progress"). Vi venter på markør-ekkoet fra side 1 før neste enhet.
 */
let installChain: Promise<void> = Promise.resolve();
/** Appen starter pluginen før profilsystemet sitt er klart; en import som sendes da låser appens importkø. Vent derfor litt. */
const PLUGIN_STARTED_AT = Date.now();
const FIRST_INSTALL_DELAY_MS = 15000;
function queueFirstInstall(d: DeviceLike): void {
	installChain = installChain.then(async () => {
		await new Promise((r) => setTimeout(r, Math.max(0, PLUGIN_STARTED_AT + FIRST_INSTALL_DELAY_MS - Date.now())));
		await jumpTo(d, 1, "first-run install");
		const deadline = Date.now() + 15000;
		while (pendingEcho.has(d.id) && Date.now() < deadline) await new Promise((r) => setTimeout(r, 250));
		if (pendingEcho.has(d.id)) {
			pendingEcho.delete(d.id);
			streamDeck.logger.warn(`DeckSync: no page marker reported on ${d.name} after install, will retry on next start`);
			return;
		}
		installed = [...installed, d.id];
		void saveGlobals();
		streamDeck.logger.info(`DeckSync: profile installed and confirmed on ${d.name}`);
	});
}

scanPageNames();
watchPageNames(() => {
	void saveGlobals();
	void refreshAll();
});

/** Når en innstillingsside åpnes: les sidenavn på nytt så listene er ferske. */
streamDeck.ui.onDidAppear(() => {
	scanPageNames();
	void saveGlobals();
});

streamDeck.devices.onDeviceDidConnect(async (ev) => {
	const d = ev.device;
	const profile = PROFILE_BY_TYPE.get(d.type);
	streamDeck.logger.info(`DeckSync: device "${d.name}" id=${d.id} type=${d.type} → ${profile ?? "no DeckSync profile"}`);
	await globalsLoaded;
	void saveGlobals(); // oppdaterer enhetslisten for innstillingssiden
	await refreshAll();

	// Første gang vi ser et deck: bytt det til DeckSync-profilen, så appen installerer den (med markører på alle sider).
	if (profile && !installed.includes(d.id)) queueFirstInstall(d);
});

streamDeck.devices.onDeviceDidDisconnect(async (ev) => {
	currentPage.delete(ev.device.id);
	pendingEcho.delete(ev.device.id);
	if (target !== "all" && !syncable().some((d) => d.id === target)) target = "all";
	void saveGlobals();
	await refreshAll();
});
