export enum DeviceType { StreamDeck = 0, StreamDeckPlus = 7 }
export const calls: any[] = []; export const registry: Record<string, any> = {};
const list = [{ id: "A", name: "Stream Deck Module 15", type: 0, isConnected: true }, { id: "B", name: "Stream Deck +", type: 7, isConnected: true }];
export const devices = Object.assign(list, {
  onDeviceDidConnect(_l: any) {}, onDeviceDidDisconnect(_l: any) {},
  getDeviceById(id: string) { return list.find((d) => d.id === id); },
});
export function action(def: any) { return (t: any) => { t.prototype.manifestId = def.UUID; return t; }; }
export class SingletonAction { get actions() { return []; } }
const sd = {
  devices, logger: { info() {}, error() {} },
  profiles: { async switchToProfile(...a: any[]) { calls.push(a); } },
  settings: { async getGlobalSettings() { return {}; }, async setGlobalSettings(_s: any) {}, onDidReceiveGlobalSettings(_l: any) {} },
  actions: { registerAction(a: any) { registry[a.manifestId] = a; } },
  ui: { onDidAppear(_l: any) {} },
  async connect() {},
};
export default sd;
