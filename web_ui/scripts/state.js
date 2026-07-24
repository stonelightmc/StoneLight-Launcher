window.SLLState = {
  launcher: { name: "StoneLight Launcher", version: "0.6.69" },
  preferences: {
    theme: "dark",
    language: "en",
    available_themes: ["dark", "light", "laconic", "neon", "retro_future"],
    available_languages: ["en", "uk", "kk"]
  },
  instances: [],
  selected_instance_id: "",
  selected_instance: null,
  official_offer: {
    available: true,
    name: "StoneLight",
    minecraft_version: "26.1.2",
    loader: "fabric",
    loader_version: "0.19.3"
  },
  accounts: [],
  selected_account_id: "",
  selected_account: null,
  java: { preset: "auto", manual_path: "" },
  global_launch: { ram_min_mb: 512, ram_max_mb: 4096, fullscreen: false },
  status: { busy: false, message: "Ready.", progress: 0 },
  activeTab: "instances",
  contextInstanceId: "",
  logs: []
};

window.SLLMockState = {
  ...window.SLLState,
  instances: [
    {
      id: "stonelight",
      name: "StoneLight",
      official: true,
      locked: true,
      minecraft_version: "26.1.2",
      loader: "fabric",
      loader_version: "0.19.3",
      java_preset: "auto",
      icon: "",
      installed: true,
      running: false
    },
    {
      id: "fabric-test",
      name: "Fabric Test",
      official: false,
      locked: false,
      minecraft_version: "1.21.11",
      loader: "fabric",
      loader_version: "",
      java_preset: "java21",
      icon: "",
      installed: false,
      running: false
    }
  ],
  selected_instance_id: "stonelight",
  selected_instance: {
    id: "stonelight",
    name: "StoneLight",
    official: true,
    minecraft_version: "26.1.2",
    loader: "fabric",
    loader_version: "0.19.3",
    java_preset: "auto",
    installed: true,
    running: false
  },
  official_offer: { available: false },
  accounts: [],
  selected_account: null
};
