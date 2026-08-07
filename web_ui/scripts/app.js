(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const app = {
    editorMode: "create",
    editorInstanceId: "",
    versionPickerTarget: "",
    versionPickerValues: [],
    editorLocked: false,
    accountManagerSelectedId: "",
    instanceWindowId: "",
    instanceWindowData: null,
    currentFolderKey: "mods",
    screenshotPreviewFiles: [],
    screenshotPreviewIndex: -1,
    launchSettingsLoaded: false,
    updateCenterData: null,
    updateAutoCheckData: null,
    iconPickerInstanceId: "",
    iconPickerIcons: [],
    iconPickerCategories: ["All"],
    iconPickerCategory: "All",
    iconPickerSelected: "",
    modrinthResults: [],
    modrinthLastTotal: 0,
    modrinthCurrentPage: 1,
    modrinthTotalPages: 1,
    modrinthPageSize: 24,
    modrinthSearched: false,
    modrinthFilterOptions: null,
    modrinthFilterKey: "",
    modrinthFilterLoading: false,
    curseforgeResults: [],
    curseforgeLastTotal: 0,
    curseforgeCurrentPage: 1,
    curseforgeTotalPages: 1,
    curseforgePageSize: 24,
    curseforgeSearched: false,
    curseforgeFilterOptions: null,
    curseforgeFilterKey: "",
    curseforgeRenderedFilterKey: "",
    curseforgeFilterLoading: false,
    applyingGraphicsProfile: false,
    graphicsProfiles: {
      unchanged: {
        render_distance: "",
        simulation_distance: "",
        fps_limit: "",
        vsync: "unchanged",
        graphics: "unchanged",
        particles: "unchanged"
      },
      performance: {
        render_distance: "8",
        simulation_distance: "5",
        fps_limit: "120",
        vsync: "off",
        graphics: "fast",
        particles: "minimal"
      },
      balanced: {
        render_distance: "12",
        simulation_distance: "8",
        fps_limit: "144",
        vsync: "unchanged",
        graphics: "fancy",
        particles: "decreased"
      },
      quality: {
        render_distance: "16",
        simulation_distance: "10",
        fps_limit: "240",
        vsync: "on",
        graphics: "fabulous",
        particles: "all"
      }
    },

    async init() {
      this.bindStaticEvents();

      try {
        if (window.SLLApi.desktopMode) {
          window.SLLState.status = {
            busy: true,
            message: "Connecting to Python...",
            progress: 0
          };
          this.renderStatus(window.SLLState.status);
          await window.SLLApi.waitUntilReady(15000);
        }

        const state = await window.SLLApi.call("get_app_state");
        this.setState(state);
        window.setTimeout(() => this.maybeAutoCheckUpdates(), 650);
      } catch (error) {
        const message = error?.message || String(error);
        this.toast(message, true);
        this.appendLog(message);

        if (window.SLLApi.desktopMode) {
          this.setState({
            ...window.SLLState,
            instances: [],
            selected_instance_id: "",
            selected_instance: null,
            official_offer: { available: false },
            status: {
              busy: false,
              error: true,
              message: message,
              progress: 0
            }
          });
        } else {
          this.setState(structuredClone(window.SLLMockState));
        }
      }
    },

    setState(nextState) {
      window.SLLState = {
        ...window.SLLState,
        ...nextState,
        activeTab: window.SLLState.activeTab || "instances",
        logs: window.SLLState.logs || []
      };
      this.applyTheme();
      this.applyLanguage();
      this.render();
    },

    render() {
      this.renderMenuControls();
      this.renderHero();
      this.renderInstances();
      this.renderAccount();
      this.renderJava();
      this.renderOfficialCta();
      this.renderModrinth();
      this.renderCurseForge();
      this.renderStatus(window.SLLState.status || {});
      this.updateActionStates();
      this.renderUpdateIndicator();
      $("#versionLabel").textContent = `v${window.SLLState.launcher?.version || "0.6.71"}`;
    },

    renderMenuControls() {
      const themes = window.SLLState.preferences.available_themes || [];
      const themeSelect = $("#themeSelect");
      themeSelect.innerHTML = themes.map(theme =>
        `<option value="${this.escape(theme)}">${this.escape(this.prettyTheme(theme))}</option>`
      ).join("");
      themeSelect.value = window.SLLState.preferences.theme || "dark";

      const languageSelect = $("#languageSelect");
      const labels = { en: "English", uk: "Українська", kk: "Қазақша" };
      languageSelect.innerHTML = (window.SLLState.preferences.available_languages || ["en", "uk", "kk"])
        .map(lang => `<option value="${lang}">${labels[lang] || lang}</option>`)
        .join("");
      languageSelect.value = window.SLLState.preferences.language || "en";
    },

    renderHero() {
      const instance = window.SLLState.selected_instance;
      const title = $("#heroTitle");
      const subtitle = $("#heroSubtitle");
      const chips = $("#heroChips");

      if (instance) {
        title.textContent = instance.name;
        const loader = instance.loader === "vanilla"
          ? "Vanilla"
          : `${this.capitalize(instance.loader)}${instance.loader_version ? ` ${instance.loader_version}` : ""}`;
        subtitle.textContent = `· Minecraft ${instance.minecraft_version} · ${loader}`;
        chips.innerHTML = [
          `<span class="chip">${this.t(instance.official ? "tile.official" : "tile.custom")}</span>`,
          `<span class="chip">${this.t(instance.installed ? "tile.installed" : "tile.notInstalled")}</span>`,
          instance.running ? `<span class="chip">${this.t("tile.running")}</span>` : ""
        ].join("");
      } else {
        title.textContent = "—";
        subtitle.textContent = this.t("hero.empty");
        chips.innerHTML = "";
      }
    },

    instanceIconHtml(instance, extraClass = "") {
      const url = instance?.icon_url || "";
      const letter = this.escape((instance?.name || "I").slice(0, 1).toUpperCase());
      const className = `instance-tile__icon${extraClass ? ` ${extraClass}` : ""}`;
      if (url) {
        return `<div class="${className} instance-tile__icon--image"><img src="${this.escape(url)}" alt="" loading="lazy" onerror="this.closest('.instance-tile__icon').textContent='${letter}'"></div>`;
      }
      return `<div class="${className}">${letter}</div>`;
    },

    renderInstances() {
      const grid = $("#instancesGrid");
      const instances = window.SLLState.instances || [];
      const selectedId = window.SLLState.selected_instance_id;

      grid.innerHTML = instances.map((instance, index) => {
        const selected = instance.id === selectedId ? " is-selected" : "";
        const loader = instance.loader === "vanilla" ? "Vanilla" : this.capitalize(instance.loader);
        return `
          <article class="instance-tile${selected}" data-instance-id="${this.escape(instance.id)}" style="animation-delay:${Math.min(index * 24, 160)}ms">
            <div class="instance-tile__top">
              ${this.instanceIconHtml(instance)}
              <button class="instance-tile__menu" data-instance-menu="${this.escape(instance.id)}" aria-label="Menu">•••</button>
            </div>
            <div>
              <div class="instance-tile__title">${this.escape(instance.name)}</div>
              <div class="instance-tile__meta">Minecraft ${this.escape(instance.minecraft_version)} · ${this.escape(loader)}</div>
            </div>
            <div class="instance-tile__footer">
              <span>${this.t(instance.official ? "tile.official" : "tile.custom")}</span>
              <span>${this.t(instance.installed ? "tile.installed" : "tile.notInstalled")}</span>
            </div>
          </article>
        `;
      }).join("");

      grid.insertAdjacentHTML("beforeend", `
        <article class="instance-tile instance-tile--add" data-add-instance>
          <div class="tile-add__plus">＋</div>
          <div class="instance-tile__title">${this.t("tile.add")}</div>
        </article>
      `);

      $("#emptyState").classList.toggle("hidden", instances.length > 0);
      grid.classList.toggle("hidden", instances.length === 0);
    },

    renderAccount() {
      const account = window.SLLState.selected_account;
      $("#accountCard").innerHTML = account
        ? `
          <div class="account-profile">
            <span class="account-profile__avatar account-avatar">
              <img src="${this.escape(account.avatar_url || "https://crafthead.net/helm/Steve")}" alt="" loading="lazy" onerror="this.src='https://crafthead.net/helm/Steve'">
            </span>
            <div>
              <div class="account-profile__name">${this.escape(account.username)}</div>
              <div class="account-profile__type">${this.t(account.licensed ? "account.licensed" : "account.offline")}</div>
            </div>
          </div>
        `
        : `
          <div class="account-profile">
            <span class="account-profile__avatar">?</span>
            <div>
              <div class="account-profile__name">${this.t("account.none")}</div>
              <div class="account-profile__type">${this.t("account.manage")}</div>
            </div>
          </div>
        `;

      const select = $("#accountSelect");
      const accounts = window.SLLState.accounts || [];
      select.innerHTML = accounts.length
        ? accounts.map(item =>
            `<option value="${this.escape(item.id)}">${this.escape(item.username)}</option>`
          ).join("")
        : `<option value="">${this.t("account.none")}</option>`;
      select.disabled = accounts.length === 0;
      select.value = window.SLLState.selected_account_id || "";
    },

    renderJava() {
      const launch = window.SLLState.global_launch || {};
      const windowMode = launch.window_mode || "unchanged";
      const size = launch.window_width && launch.window_height
        ? `${launch.window_width}×${launch.window_height}`
        : this.t("launch.defaultSize");
      const renderDistance = launch.render_distance ? `${launch.render_distance}` : this.t("launch.unchanged");
      const fps = launch.fps_limit ? `${launch.fps_limit}` : this.t("launch.unchanged");
      const profile = launch.graphics_profile || "custom";
      $("#javaSummary").innerHTML = `
        <div><dt>${this.t("java.ram")}</dt><dd>${this.escape(String(launch.ram_min_mb || 512))}–${this.escape(String(launch.ram_max_mb || 4096))} MB</dd></div>
        <div><dt>${this.t("launch.profileShort")}</dt><dd>${this.t(`launch.profileValue.${profile}`)}</dd></div>
        <div><dt>${this.t("launch.windowMode")}</dt><dd>${this.t(`launch.${windowMode}`)}</dd></div>
        <div><dt>${this.t("launch.windowSize")}</dt><dd>${this.escape(size)}</dd></div>
        <div><dt>${this.t("launch.renderDistanceShort")}</dt><dd>${this.escape(renderDistance)}</dd></div>
        <div><dt>${this.t("launch.fpsShort")}</dt><dd>${this.escape(fps)}</dd></div>
      `;
    },

    renderOfficialCta() {
      const hasAnyInstance = (window.SLLState.instances || []).length > 0;
      $("#officialCta").classList.toggle(
        "hidden",
        !window.SLLState.official_offer?.available || !hasAnyInstance
      );
    },

    renderStatus(status) {
      const busy = Boolean(status.busy);
      const dot = $("#statusDot");
      dot.classList.toggle("is-busy", busy);
      dot.classList.toggle("is-error", Boolean(status.error));
      $("#statusText").textContent = status.message ? this.localizeMessage(status.message) : this.t("status.ready");
      const progress = Math.max(0, Math.min(1, Number(status.progress || 0)));
      $("#progressBar").style.width = `${progress * 100}%`;
    },

    updateActionStates() {
      const instance = window.SLLState.selected_instance;
      const busy = Boolean(window.SLLState.status?.busy);
      const play = $('[data-action="play"]');
      const install = $('[data-action="install"]');
      const stop = $('[data-action="stop"]');

      play.disabled = !instance || busy || instance.running;
      install.disabled = !instance || busy;
      stop.disabled = !instance || (!instance.running && !busy);
      $$("[data-action]").forEach(button => {
        if (button.dataset.action === "stop") return;
        if (button.dataset.action === "official_install") {
          button.disabled = busy;
        }
      });
    },

    applyTheme() {
      document.documentElement.dataset.theme = window.SLLState.preferences?.theme || "dark";
    },

    applyLanguage() {
      document.documentElement.lang = window.SLLState.preferences?.language || "en";
      $$("[data-i18n]").forEach(element => {
        element.textContent = this.t(element.dataset.i18n);
      });
      $$("[data-i18n-title]").forEach(element => {
        element.title = this.t(element.dataset.i18nTitle);
      });
      $$("[data-i18n-placeholder]").forEach(element => {
        element.placeholder = this.t(element.dataset.i18nPlaceholder);
      });
    },

    switchTab(tabName) {
      this.closeMenus();
      this.hideContextMenu();
      window.SLLState.activeTab = tabName;
      $$(".tab").forEach(tab => tab.classList.toggle("is-active", tab.dataset.tab === tabName));
      $$("[data-tab-content]").forEach(panel =>
        panel.classList.toggle("is-active", panel.dataset.tabContent === tabName)
      );
      if (tabName === "modrinth") {
        this.renderModrinth();
      }
      if (tabName === "curseforge") {
        this.renderCurseForge();
      }
    },

    bindStaticEvents() {
      document.addEventListener("click", event => this.handleClick(event));
      document.addEventListener("contextmenu", event => this.handleContextMenu(event));
      document.addEventListener("scroll", () => this.hideContextMenu(), true);
      window.addEventListener("resize", () => this.hideContextMenu());
      window.addEventListener("blur", () => {
        this.closeMenus();
        this.hideContextMenu();
      });
      document.addEventListener("keydown", event => {
        if (!$("#screenshotPreviewBackdrop").classList.contains("hidden") && event.key === "ArrowLeft") {
          this.showAdjacentScreenshot(-1);
          return;
        }
        if (!$("#screenshotPreviewBackdrop").classList.contains("hidden") && event.key === "ArrowRight") {
          this.showAdjacentScreenshot(1);
          return;
        }

        if (event.key === "Escape") {
          if (!$("#screenshotPreviewBackdrop").classList.contains("hidden")) {
            this.closeScreenshotPreview();
          } else if (!$("#versionPickerBackdrop").classList.contains("hidden")) {
            this.closeVersionPicker();
          } else if (!$("#iconPickerBackdrop").classList.contains("hidden")) {
            this.closeIconPicker();
          } else if (!$("#instanceEditorBackdrop").classList.contains("hidden")) {
            this.closeInstanceEditor();
          } else if (!$("#updateCenterBackdrop").classList.contains("hidden")) {
            this.closeUpdateCenter();
          } else if (!$("#launchSettingsBackdrop").classList.contains("hidden")) {
            this.closeLaunchSettings();
          } else if (!$("#accountManagerBackdrop").classList.contains("hidden")) {
            this.closeAccountManager();
          } else if (!$("#instanceWindowBackdrop").classList.contains("hidden")) {
            this.closeInstanceWindow();
          }
          this.closeMenus();
          this.hideContextMenu();
        }
      });

      $("#themeSelect").addEventListener("change", async event => {
        const value = event.target.value;
        window.SLLState.preferences.theme = value;
        this.applyTheme();
        await window.SLLApi.call("set_preference", "theme", value);
      });

      $("#languageSelect").addEventListener("change", async event => {
        const value = event.target.value;
        window.SLLState.preferences.language = value;
        this.applyLanguage();
        this.render();
        await window.SLLApi.call("set_preference", "language", value);
      });

      $("#instanceEditorClose")?.addEventListener("click", () => this.closeInstanceEditor());
      $("#instanceEditorCancel")?.addEventListener("click", () => this.closeInstanceEditor());
      $("#instanceEditorBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "instanceEditorBackdrop") this.closeInstanceEditor();
      });
      $("#instanceEditorForm")?.addEventListener("submit", event => this.submitInstanceEditor(event));
      $("#deleteInstanceButton")?.addEventListener("click", () => this.deleteEditedInstance());
      $("#instanceLoaderSelect")?.addEventListener("change", () => {
        this.syncInstanceEditorFields();
        this.loadLoaderVersionOptions();
      });
      $("#instanceJavaPresetSelect")?.addEventListener("change", () => this.syncInstanceEditorFields());
      $("#instanceVersionTypeSelect")?.addEventListener("change", () => this.loadMinecraftVersionOptions());
      $("#instanceMinecraftInput")?.addEventListener("change", () => this.loadLoaderVersionOptions());
      $("#loadMinecraftVersionsButton")?.addEventListener("click", () => this.loadMinecraftVersionOptions());
      $("#loadLoaderVersionsButton")?.addEventListener("click", () => this.loadLoaderVersionOptions());

      $("#versionPickerClose")?.addEventListener("click", () => this.closeVersionPicker());
      $("#versionPickerBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "versionPickerBackdrop") this.closeVersionPicker();
      });
      $("#versionPickerFilter")?.addEventListener("input", () => this.renderVersionPickerList());

      $("#iconPickerClose")?.addEventListener("click", () => this.closeIconPicker());
      $("#iconPickerCancel")?.addEventListener("click", () => this.closeIconPicker());
      $("#iconPickerBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "iconPickerBackdrop") this.closeIconPicker();
      });
      $("#iconPickerSearch")?.addEventListener("input", () => this.renderIconPicker());
      $("#iconPickerClear")?.addEventListener("click", () => {
        $("#iconPickerSearch").value = "";
        this.iconPickerCategory = "All";
        this.renderIconPicker();
      });
      $("#iconPickerReset")?.addEventListener("click", () => this.resetInstanceIcon());

      $("#instanceWindowClose")?.addEventListener("click", () => this.closeInstanceWindow());
      $("#instanceWindowBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "instanceWindowBackdrop") this.closeInstanceWindow();
      });
      $$("[data-instance-window-tab]").forEach(button => {
        button.addEventListener("click", () => this.switchInstanceWindowTab(button.dataset.instanceWindowTab));
      });
      $$("[data-instance-window-action]").forEach(button => {
        button.addEventListener("click", () => this.runInstanceWindowAction(button.dataset.instanceWindowAction));
      });
      $("#refreshFolderButton")?.addEventListener("click", () => this.refreshCurrentFolder());
      $("#openCurrentFolderButton")?.addEventListener("click", () => this.openInstanceSubfolder(this.currentFolderKey));
      $("#screenshotPreviewClose")?.addEventListener("click", () => this.closeScreenshotPreview());
      $("#screenshotPreviewPrev")?.addEventListener("click", () => this.showAdjacentScreenshot(-1));
      $("#screenshotPreviewNext")?.addEventListener("click", () => this.showAdjacentScreenshot(1));
      $("#screenshotPreviewBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "screenshotPreviewBackdrop") this.closeScreenshotPreview();
      });
      $("#instanceWindowSettingsForm")?.addEventListener("submit", event => this.submitWindowSettings(event));
      $("#windowSettingsJavaPreset")?.addEventListener("change", () => this.syncWindowSettingsFields());
      $("#windowSettingsLoader")?.addEventListener("change", () => {
        this.syncWindowSettingsFields();
        this.loadWindowLoaderVersionOptions();
      });
      $("#windowSettingsVersionType")?.addEventListener("change", () => this.loadWindowMinecraftVersionOptions());
      $("#windowSettingsMinecraft")?.addEventListener("change", () => this.loadWindowLoaderVersionOptions());
      $("#windowSettingsLoadMinecraftVersionsButton")?.addEventListener("click", () => this.loadWindowMinecraftVersionOptions());
      $("#windowSettingsLoadLoaderVersionsButton")?.addEventListener("click", () => this.loadWindowLoaderVersionOptions());

      $("#updateCenterClose")?.addEventListener("click", () => this.closeUpdateCenter());
      $("#updateCenterCancel")?.addEventListener("click", () => this.closeUpdateCenter());
      $("#updateCenterBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "updateCenterBackdrop") this.closeUpdateCenter();
      });
      $("#updateCenterRefresh")?.addEventListener("click", () => this.checkUpdatesAndShow(true));
      $("#updateLauncherButton")?.addEventListener("click", () => this.applyLauncherUpdate());
      $("#updateOfficialButton")?.addEventListener("click", () => this.applyOfficialUpdate());

      $("#aboutClose")?.addEventListener("click", () => this.closeAboutDialog());
      $("#aboutCloseFooter")?.addEventListener("click", () => this.closeAboutDialog());
      $("#aboutBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "aboutBackdrop") this.closeAboutDialog();
      });

      $("#launchSettingsClose")?.addEventListener("click", () => this.closeLaunchSettings());
      $("#launchSettingsCancel")?.addEventListener("click", () => this.closeLaunchSettings());
      $("#launchSettingsBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "launchSettingsBackdrop") this.closeLaunchSettings();
      });
      $("#modrinthSearchForm")?.addEventListener("submit", event => this.searchModrinth(event, 1));
      $("#modrinthTypeSelect")?.addEventListener("change", () => {
        this.modrinthFilterOptions = null;
        this.modrinthFilterKey = "";
        this.modrinthCurrentPage = 1;
        this.modrinthTotalPages = 1;
        this.renderModrinth();
        this.loadModrinthFilters();
      });
      $("#modrinthResetFiltersButton")?.addEventListener("click", () => this.resetModrinthFilters());
      $("#modrinthShowSnapshotsCheckbox")?.addEventListener("change", () => {
        this.modrinthFilterOptions = null;
        this.modrinthFilterKey = "";
        this.loadModrinthFilters();
        if (this.modrinthSearched) this.searchModrinth(null, 1);
      });
      $("#modrinthSortSelect")?.addEventListener("change", () => {
        if (this.modrinthSearched) this.searchModrinth(null, 1);
      });

      $("#curseforgeSearchForm")?.addEventListener("submit", event => this.searchCurseForge(event, 1));
      $("#curseforgeTypeSelect")?.addEventListener("change", () => {
        this.curseforgeCurrentPage = 1;
        this.curseforgeTotalPages = 1;
        this.curseforgeFilterOptions = null;
        this.curseforgeFilterKey = "";
        this.curseforgeRenderedFilterKey = "";
        this.loadCurseForgeFilters();
        if (this.curseforgeSearched) {
          this.searchCurseForge(null, 1);
        } else {
          this.renderCurseForge();
        }
      });
      $("#curseforgeSortSelect")?.addEventListener("change", () => {
        if (this.curseforgeSearched) this.searchCurseForge(null, 1);
      });
      $("#curseforgeShowManualOnlyCheckbox")?.addEventListener("change", () => {
        if (this.curseforgeSearched) this.searchCurseForge(null, 1);
      });
      $("#curseforgeShowSnapshotsCheckbox")?.addEventListener("change", () => {
        this.curseforgeFilterOptions = null;
        this.curseforgeFilterKey = "";
        this.curseforgeRenderedFilterKey = "";
        this.loadCurseForgeFilters();
        if (this.curseforgeSearched) this.searchCurseForge(null, 1);
      });
      $("#curseforgeResetFiltersButton")?.addEventListener("click", () => this.resetCurseForgeFilters());

      $("#launchSettingsForm")?.addEventListener("submit", event => this.submitLaunchSettings(event));
      $("#launchSettingsReset")?.addEventListener("click", () => this.resetLaunchSettingsForm());
      $("#globalGraphicsProfileSelect")?.addEventListener("change", () => this.applySelectedGraphicsProfile());
      [
        "#globalRenderDistanceInput",
        "#globalSimulationDistanceInput",
        "#globalFpsLimitInput",
        "#globalVsyncSelect",
        "#globalGraphicsSelect",
        "#globalParticlesSelect"
      ].forEach(selector => {
        $(selector)?.addEventListener("input", () => this.markGraphicsProfileCustom());
        $(selector)?.addEventListener("change", () => this.markGraphicsProfileCustom());
      });
      $("#accountManagerClose")?.addEventListener("click", () => this.closeAccountManager());
      $("#accountManagerBackdrop")?.addEventListener("click", event => {
        if (event.target.id === "accountManagerBackdrop") this.closeAccountManager();
      });
      $("#addMicrosoftAccountButton")?.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
        this.addMicrosoftAccount();
      });
      $("#addOfflineAccountButton")?.addEventListener("click", () => this.addOfflineAccount());
      $("#deleteAccountButton")?.addEventListener("click", () => this.deleteSelectedAccount());
      $("#refreshAccountButton")?.addEventListener("click", () => this.refreshSelectedAccount());
      $("#offlineAccountNameInput")?.addEventListener("keydown", event => {
        if (event.key === "Enter") this.addOfflineAccount();
      });

      $("#accountSelect").addEventListener("change", async event => {
        const result = await window.SLLApi.call("select_account", event.target.value);
        if (result?.ok && result.state) {
          this.setState(result.state);
        } else if (result?.error) {
          this.toast(result.error, true);
        }
      });
    },

    async handleClick(event) {
      const clickedInsideContextMenu = Boolean(event.target.closest("#contextMenu"));
      const clickedContextTrigger = Boolean(event.target.closest("[data-instance-menu]"));
      if (!clickedInsideContextMenu && !clickedContextTrigger) {
        this.hideContextMenu();
      }

      const menuTrigger = event.target.closest("[data-menu]");
      if (menuTrigger) {
        const menu = menuTrigger.closest(".menu");
        const willOpen = !menu.classList.contains("is-open");
        this.closeMenus();
        menu.classList.toggle("is-open", willOpen);
        return;
      }

      if (!event.target.closest(".menu")) {
        this.closeMenus();
      }

      const tab = event.target.closest("[data-tab]");
      if (tab) {
        this.switchTab(tab.dataset.tab);
        return;
      }

      const tile = event.target.closest("[data-instance-id]");
      if (tile && !event.target.closest("[data-instance-menu]")) {
        await this.selectInstance(tile.dataset.instanceId);
        return;
      }

      const menuButton = event.target.closest("[data-instance-menu]");
      if (menuButton) {
        const rect = menuButton.getBoundingClientRect();
        this.showContextMenu(menuButton.dataset.instanceMenu, rect.left, rect.bottom + 4);
        return;
      }

      if (event.target.closest("[data-add-instance]")) {
        await this.openInstanceEditor();
        return;
      }

      const actionButton = event.target.closest("[data-action]");
      if (actionButton) {
        await this.runAction(actionButton.dataset.action);
        return;
      }

      const commandButton = event.target.closest("[data-command]");
      if (commandButton) {
        await this.runCommand(commandButton.dataset.command);
        return;
      }

      const contextButton = event.target.closest("[data-context-action]");
      if (contextButton) {
        await this.runContextAction(contextButton.dataset.contextAction);
      }
    },

    handleContextMenu(event) {
      const tile = event.target.closest("[data-instance-id]");
      if (!tile) {
        this.hideContextMenu();
        return;
      }
      event.preventDefault();
      this.showContextMenu(tile.dataset.instanceId, event.clientX, event.clientY);
    },

    async selectInstance(instanceId) {
      const result = await window.SLLApi.call("select_instance", instanceId);
      if (result?.ok && result.state) {
        this.setState(result.state);
        this.toast(this.t("toast.selected"));
      } else {
        this.toast(result?.error || this.t("error.generic"), true);
      }
    },

    updateCheckStorageKey() {
      const version = window.SLLState.launcher?.version || "0";
      return `stonelight.updateCheck.v2.${version}`;
    },

    readUpdateCheckStamp() {
      try {
        const raw = window.localStorage.getItem(this.updateCheckStorageKey()) || "0";
        return Number(raw || 0) || 0;
      } catch (_error) {
        return 0;
      }
    },

    writeUpdateCheckStamp() {
      try {
        window.localStorage.setItem(this.updateCheckStorageKey(), String(Date.now()));
      } catch (_error) {}
    },

    async maybeAutoCheckUpdates() {
      const launcher = window.SLLState.launcher || {};
      if (launcher.autocheck_updates === false) return;

      const intervalHours = Math.max(1, Number(launcher.update_autocheck_interval_hours || 24));
      const last = this.readUpdateCheckStamp();
      if (last && Date.now() - last < intervalHours * 60 * 60 * 1000) {
        return;
      }

      await this.runSilentUpdateCheck();
    },

    async runSilentUpdateCheck() {
      try {
        const result = await window.SLLApi.call("run_action", "check_updates");
        this.writeUpdateCheckStamp();

        if (!result?.ok) {
          this.appendLog(`[updates] ${this.localizeMessage(result?.error || this.t("error.generic"))}`);
          return;
        }

        this.updateAutoCheckData = result;
        this.updateCenterData = result;
        this.renderUpdateIndicator();

        const available = Boolean(result.launcher?.has_update || result.official?.has_update);
        if (available) {
          this.appendLog("[updates] Update available.");
          this.toast(this.t("updates.available"));
        } else {
          this.appendLog("[updates] No updates found.");
        }
      } catch (error) {
        this.writeUpdateCheckStamp();
        this.appendLog(`[updates] ${error?.message || String(error)}`);
      }
    },

    renderUpdateIndicator() {
      const data = this.updateAutoCheckData || this.updateCenterData;
      const available = Boolean(data?.launcher?.has_update || data?.official?.has_update);
      $$('[data-action="check_updates"], [data-command="check-updates"]').forEach(button => {
        button.classList.toggle("has-update-indicator", available);
        if (available) {
          button.title = this.t("updates.available");
        } else if (button.title === this.t("updates.available")) {
          button.removeAttribute("title");
        }
      });
    },

    openUpdateCenter() {
      const backdrop = $("#updateCenterBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");

      if (this.updateCenterData) {
        this.renderUpdateCenter(this.updateCenterData);
        const available = Boolean(this.updateCenterData.launcher?.has_update || this.updateCenterData.official?.has_update);
        this.setUpdateCenterStatus(this.t(available ? "updates.available" : "updates.none"), false);
      }
    },

    closeUpdateCenter() {
      const backdrop = $("#updateCenterBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
    },

    async checkUpdatesAndShow(manualRefresh = false) {
      this.closeMenus();
      this.hideContextMenu();
      this.openUpdateCenter();
      this.setUpdateCenterStatus(this.t("updates.checking"), false);

      const refreshButton = $("#updateCenterRefresh");
      refreshButton.disabled = true;

      try {
        const result = await window.SLLApi.call("run_action", "check_updates");
        if (!result?.ok) {
          this.setUpdateCenterStatus(result?.error || this.t("error.generic"), true);
          return;
        }

        this.writeUpdateCheckStamp();
        this.updateCenterData = result;
        this.updateAutoCheckData = result;
        this.renderUpdateCenter(result);
        this.renderUpdateIndicator();
        const available = Boolean(result.launcher?.has_update || result.official?.has_update);
        this.setUpdateCenterStatus(this.t(available ? "updates.available" : "updates.none"), false);
        if (manualRefresh) this.toast(this.t(available ? "updates.available" : "updates.none"));
      } catch (error) {
        this.setUpdateCenterStatus(error?.message || String(error), true);
      } finally {
        refreshButton.disabled = false;
      }
    },

    setUpdateCenterStatus(message, isError = false) {
      const box = $("#updateCenterStatus");
      box.textContent = message ? this.localizeMessage(message) : "";
      box.classList.toggle("hidden", !message);
      box.classList.toggle("form-error", Boolean(isError));
      box.classList.toggle("form-note", !isError);
    },

    renderUpdateCenter(data) {
      this.renderUpdateCard("launcher", data.launcher || {});
      this.renderUpdateCard("official", data.official || {});
    },

    renderUpdateCard(kind, info) {
      const isLauncher = kind === "launcher";
      const title = $(`#${kind}UpdateTitle`);
      const badge = $(`#${kind}UpdateBadge`);
      const details = $(`#${kind}UpdateDetails`);
      const button = isLauncher ? $("#updateLauncherButton") : $("#updateOfficialButton");

      const notInstalled = !isLauncher && Boolean(info.not_installed);
      const hasUpdate = Boolean(info.has_update);
      const warning = info.warning || "";
      const statusKey = notInstalled
        ? "updates.notInstalledShort"
        : (warning ? "updates.warning" : (hasUpdate ? "updates.availableShort" : "updates.currentShort"));

      badge.textContent = this.t(statusKey);
      badge.classList.toggle("is-update", hasUpdate && !notInstalled);
      badge.classList.toggle("is-warning", Boolean(warning) || notInstalled);

      title.textContent = notInstalled
        ? this.t("updates.officialNotInstalled")
        : (warning ? warning : this.t(hasUpdate ? "updates.updateFound" : "updates.upToDate"));

      const rows = isLauncher
        ? [
            [this.t("updates.currentVersion"), info.current_version || "?"],
            [this.t("updates.latestVersion"), info.latest_version || "?"],
            [this.t("updates.asset"), info.asset_name || this.t("updates.noAsset")]
          ]
        : (notInstalled
          ? [
              [this.t("updates.status"), this.t("updates.officialNotInstalled")],
              [this.t("updates.currentMinecraft"), info.current_minecraft_version || "?"]
            ]
          : [
              [this.t("updates.currentMinecraft"), info.current_minecraft_version || "?"],
              [this.t("updates.latestMinecraft"), info.latest_minecraft_version || "?"],
              [this.t("updates.installedAsset"), info.installed_archive_name || "—"],
              [this.t("updates.asset"), info.asset_name || this.t("updates.noAsset")]
            ]);

      details.innerHTML = rows.map(([label, value]) => `
        <div>
          <dt>${this.escape(label)}</dt>
          <dd>${this.escape(value)}</dd>
        </div>
      `).join("");

      button.classList.toggle("hidden", notInstalled || !hasUpdate || Boolean(warning));
      button.disabled = notInstalled || !hasUpdate || Boolean(warning);
    },

    async applyLauncherUpdate() {
      const button = $("#updateLauncherButton");
      button.disabled = true;
      this.setUpdateCenterStatus(this.t("updates.launcherApplying"), false);

      try {
        const result = await window.SLLApi.call("apply_launcher_update");
        if (!result?.ok) {
          this.setUpdateCenterStatus(result?.error || this.t("error.generic"), true);
          button.disabled = false;
          return;
        }

        this.toast(result.message || this.t("updates.launcherStarted"));
        this.setUpdateCenterStatus(result.message || this.t("updates.launcherStarted"), false);
      } catch (error) {
        this.setUpdateCenterStatus(error?.message || String(error), true);
        button.disabled = false;
      }
    },

    async applyOfficialUpdate() {
      const button = $("#updateOfficialButton");
      button.disabled = true;
      this.setUpdateCenterStatus(this.t("updates.officialApplying"), false);

      try {
        const result = await window.SLLApi.call("apply_official_update");
        if (!result?.ok) {
          this.setUpdateCenterStatus(result?.error || this.t("error.generic"), true);
          button.disabled = false;
          return;
        }

        this.toast(result.message || this.t("updates.officialStarted"));
        this.setUpdateCenterStatus(result.message || this.t("updates.officialStarted"), false);
        this.closeUpdateCenter();
        await this.refreshAppState(false);
      } catch (error) {
        this.setUpdateCenterStatus(error?.message || String(error), true);
        button.disabled = false;
      }
    },

    selectedInstanceForCatalog() {
      return window.SLLState.selected_instance || null;
    },

    modrinthTypeLabel(type) {
      const key = {
        mod: "modrinth.typeModOne",
        resourcepack: "modrinth.typeResourcepackOne",
        shader: "modrinth.typeShaderOne",
        modpack: "modrinth.typeModpackOne"
      }[type] || "modrinth.project";
      return this.t(key);
    },

    renderModrinth() {
      const selected = this.selectedInstanceForCatalog();
      const info = $("#modrinthSelectedInstance");
      if (info) {
        if (selected) {
          const loader = selected.loader === "vanilla" ? "Vanilla" : this.capitalize(selected.loader || "");
          info.innerHTML = `
            <span>${this.t("modrinth.target")}</span>
            <strong>${this.escape(selected.name)} · ${this.escape(selected.minecraft_version || "?")} · ${this.escape(loader)}</strong>
          `;
        } else {
          info.innerHTML = `<span>${this.t("modrinth.noTarget")}</span>`;
        }
      }

      const type = $("#modrinthTypeSelect")?.value || "mod";
      const warning = $("#modrinthStatus");
      this.loadModrinthFilters();

      if (warning && type === "mod" && selected?.loader === "vanilla") {
        warning.textContent = this.t("modrinth.vanillaModWarning");
        warning.classList.remove("hidden");
      } else if (warning && !this.modrinthSearched) {
        warning.textContent = type === "modpack"
          ? this.t("modrinth.modpackTargetHint")
          : this.t("modrinth.readyHint");
        warning.classList.remove("hidden");
      }

      this.renderModrinthResults();
    },

    modrinthFilterRequestKey() {
      const selected = this.selectedInstanceForCatalog();
      const type = $("#modrinthTypeSelect")?.value || "mod";
      const snapshots = $("#modrinthShowSnapshotsCheckbox")?.checked ? "snapshots" : "releases";
      const language = window.SLLState?.preferences?.language || "en";
      return `${selected?.id || ""}|${selected?.minecraft_version || ""}|${selected?.loader || ""}|${type}|${snapshots}|${language}`;
    },

    async loadModrinthFilters() {
      const selected = this.selectedInstanceForCatalog();
      const type = $("#modrinthTypeSelect")?.value || "mod";
      const key = this.modrinthFilterRequestKey();

      if (!selected) {
        this.modrinthFilterOptions = null;
        this.modrinthFilterKey = "";
        this.renderModrinthFilters();
        return null;
      }

      if (this.modrinthFilterOptions && this.modrinthFilterKey === key) {
        return this.modrinthFilterOptions;
      }

      if (this.modrinthFilterLoading) return this.modrinthFilterOptions;

      this.modrinthFilterLoading = true;
      try {
        const result = await window.SLLApi.call("get_modrinth_filter_options", {
          project_type: type,
          instance_id: selected.id,
          include_snapshots: Boolean($("#modrinthShowSnapshotsCheckbox")?.checked)
        });

        if (result?.ok) {
          this.modrinthFilterOptions = result;
          this.modrinthFilterKey = key;
        } else {
          this.modrinthFilterOptions = null;
          this.modrinthFilterKey = "";
        }
      } catch (_error) {
        this.modrinthFilterOptions = null;
        this.modrinthFilterKey = "";
      } finally {
        this.modrinthFilterLoading = false;
        this.renderModrinthFilters();
      }

      return this.modrinthFilterOptions;
    },

    renderModrinthFilters() {
      const box = $("#modrinthFilters");
      const fields = $("#modrinthFilterFields");
      const groups = $("#modrinthFilterGroups");
      if (!box || !fields || !groups) return;

      const options = this.modrinthFilterOptions;
      if (!options?.ok) {
        box.classList.add("hidden");
        fields.innerHTML = "";
        groups.innerHTML = "";
        return;
      }

      box.classList.remove("hidden");
      const sections = options.sections || [];
      const selectSections = sections.filter(section => section.control === "select");
      const chipSections = sections.filter(section => section.control === "chips" && (section.choices || []).length);

      fields.innerHTML = selectSections.map(section => this.modrinthSelectFilterHtml(section)).join("");
      groups.innerHTML = chipSections.map(section => this.modrinthChipFilterHtml(section)).join("");

      fields.querySelectorAll("select[data-modrinth-filter-key]").forEach(select => {
        select.addEventListener("change", () => {
          if (this.modrinthSearched) this.searchModrinth(null, 1);
        });
      });

      groups.querySelectorAll("[data-modrinth-filter-chip]").forEach(button => {
        button.addEventListener("click", () => {
          button.classList.toggle("is-active");
          if (this.modrinthSearched) this.searchModrinth(null, 1);
        });
      });
    },

    modrinthFilterLabel(key) {
      return this.t(`modrinth.filter.${key}`);
    },

    modrinthFilterChoiceLabel(sectionKey, choice) {
      const id = String(choice?.id || "").trim();
      const raw = String(choice?.label || id).trim();
      const lang = window.SLLState?.preferences?.language || "en";
      const labels = this.modrinthChoiceLabels();
      return labels[lang]?.[id] || labels.en?.[id] || raw;
    },

    modrinthChoiceLabels() {
      return {
        en: {
          "": "Any",
          client: "Client",
          server: "Server",
          both: "Client + Server"
        },
        uk: {
          "": "Будь-який",
          client: "Клієнт",
          server: "Сервер",
          both: "Клієнт + сервер",

          application: "Приклад",
          data: "Дані",
          datapack: "Датапак",
          "data-pack": "Датапак",
          "server-side": "Серверні",
          "client-side": "Клієнтські",
          "singleplayer": "Одиночна гра",
          multiplayer: "Мультиплеєр",
          combat: "Бої",
          challenging: "Складні",
          "kitchen-sink": "Усе разом",
          lightweight: "Легкі",
          quests: "Квести",
          exploration: "Дослідження",
          "quality-of-life": "Зручність гри",
          "vanilla-plus": "Vanilla+",
          "map": "Мапа",
          "world": "Світ",

          bukkit: "Bukkit",
          spigot: "Spigot",
          paper: "Paper",
          purpur: "Purpur",
          folia: "Folia",
          sponge: "Sponge",
          velocity: "Velocity",
          waterfall: "Waterfall",
          bungeecord: "BungeeCord",
          liteloader: "LiteLoader",
          rift: "Rift",

          "any": "Будь-який",
          required: "Обов’язково",
          optional: "Опційно",
          unsupported: "Не підтримується",

          adventure: "Пригоди",
          cursed: "Дивне",
          decoration: "Декор",
          economy: "Економіка",
          equipment: "Спорядження",
          food: "Їжа",
          "game-mechanics": "Ігрові механіки",
          library: "Бібліотека",
          magic: "Магія",
          management: "Керування",
          minigame: "Мінігра",
          mobs: "Моби",
          optimization: "Оптимізація",
          social: "Соціальне",
          storage: "Зберігання",
          technology: "Технології",
          transportation: "Транспорт",
          utility: "Утиліти",
          worldgen: "Генерація світу",

          audio: "Аудіо",
          blocks: "Блоки",
          "core-shaders": "Core shaders",
          entities: "Сутності",
          environment: "Оточення",
          fonts: "Шрифти",
          gui: "Інтерфейс",
          items: "Предмети",
          locale: "Локалізація",
          models: "Моделі",
          modded: "Для модів",
          realistic: "Реалістичні",
          simplistic: "Спрощені",
          themed: "Тематичні",
          tweaks: "Твіки",

          "8x-": "8x або нижче",
          "16x": "16x",
          "32x": "32x",
          "48x": "48x",
          "64x": "64x",
          "128x": "128x",
          "256x": "256x",
          "512x+": "512x+",

          canvas: "Canvas",
          iris: "Iris",
          optifine: "OptiFine",
          vanilla: "Vanilla",
          fabric: "Fabric",
          forge: "Forge",
          neoforge: "NeoForge",
          quilt: "Quilt",

          potato: "Дуже низьке",
          low: "Низьке",
          medium: "Середнє",
          high: "Високе",
          screenshot: "Для скриншотів",
          fantasy: "Фентезі",
          "path-tracing": "Path tracing",
          pbr: "PBR",
          "vanilla-like": "Vanilla-like",
          "semi-realistic": "Напівреалістичні"
        },
        kk: {
          "": "Кез келген",
          client: "Клиент",
          server: "Сервер",
          both: "Клиент + сервер",

          application: "Қолданба",
          data: "Деректер",
          datapack: "Датапак",
          "data-pack": "Датапак",
          "server-side": "Серверлік",
          "client-side": "Клиенттік",
          "singleplayer": "Жеке ойын",
          multiplayer: "Көп ойыншы",
          combat: "Шайқас",
          challenging: "Күрделі",
          "kitchen-sink": "Бәрі бірге",
          lightweight: "Жеңіл",
          quests: "Квесттер",
          exploration: "Зерттеу",
          "quality-of-life": "Ойын ыңғайлылығы",
          "vanilla-plus": "Vanilla+",
          "map": "Карта",
          "world": "Әлем",

          bukkit: "Bukkit",
          spigot: "Spigot",
          paper: "Paper",
          purpur: "Purpur",
          folia: "Folia",
          sponge: "Sponge",
          velocity: "Velocity",
          waterfall: "Waterfall",
          bungeecord: "BungeeCord",
          liteloader: "LiteLoader",
          rift: "Rift",

          "any": "Кез келген",
          required: "Міндетті",
          optional: "Қосымша",
          unsupported: "Қолдау жоқ",

          adventure: "Шытырман оқиға",
          cursed: "Ерекше",
          decoration: "Декор",
          economy: "Экономика",
          equipment: "Жабдық",
          food: "Тағам",
          "game-mechanics": "Ойын механикалары",
          library: "Кітапхана",
          magic: "Магия",
          management: "Басқару",
          minigame: "Мини-ойын",
          mobs: "Мобтар",
          optimization: "Оңтайландыру",
          social: "Әлеуметтік",
          storage: "Сақтау",
          technology: "Технология",
          transportation: "Көлік",
          utility: "Құралдар",
          worldgen: "Әлем генерациясы",

          audio: "Аудио",
          blocks: "Блоктар",
          "core-shaders": "Core shaders",
          entities: "Нысандар",
          environment: "Орта",
          fonts: "Қаріптер",
          gui: "Интерфейс",
          items: "Заттар",
          locale: "Локализация",
          models: "Модельдер",
          modded: "Модтарға арналған",
          realistic: "Реалистік",
          simplistic: "Қарапайым",
          themed: "Тақырыптық",
          tweaks: "Түзетулер",

          "8x-": "8x немесе төмен",
          "16x": "16x",
          "32x": "32x",
          "48x": "48x",
          "64x": "64x",
          "128x": "128x",
          "256x": "256x",
          "512x+": "512x+",

          canvas: "Canvas",
          iris: "Iris",
          optifine: "OptiFine",
          vanilla: "Vanilla",
          fabric: "Fabric",
          forge: "Forge",
          neoforge: "NeoForge",
          quilt: "Quilt",

          potato: "Өте төмен",
          low: "Төмен",
          medium: "Орташа",
          high: "Жоғары",
          screenshot: "Скриншот үшін",
          fantasy: "Фэнтези",
          "path-tracing": "Path tracing",
          pbr: "PBR",
          "vanilla-like": "Vanilla-like",
          "semi-realistic": "Жартылай реалистік"
        }
      };
    },

    modrinthSelectFilterHtml(section) {
      const choices = section.choices || [];
      const defaultValue = section.default || "";
      return `
        <label class="form-field catalog-filter-field">
          <span>${this.escape(this.modrinthFilterLabel(section.key))}</span>
          <select class="select" data-modrinth-filter-key="${this.escape(section.key)}">
            ${choices.map(choice => `
              <option value="${this.escape(choice.id)}" ${choice.id === defaultValue ? "selected" : ""}>${this.escape(this.modrinthFilterChoiceLabel(section.key, choice))}</option>
            `).join("")}
          </select>
        </label>
      `;
    },

    modrinthChipFilterHtml(section) {
      const choices = section.choices || [];
      return `
        <section class="catalog-filter-group" data-modrinth-filter-group="${this.escape(section.key)}">
          <div class="catalog-filter-group__title">${this.escape(this.modrinthFilterLabel(section.key))}</div>
          <div class="catalog-filter-chips">
            ${choices.map(choice => `
              <button class="catalog-filter-chip" type="button" data-modrinth-filter-chip="${this.escape(section.key)}" data-filter-value="${this.escape(choice.id)}">
                ${this.escape(this.modrinthFilterChoiceLabel(section.key, choice))}
              </button>
            `).join("")}
          </div>
        </section>
      `;
    },

    collectModrinthFilters() {
      const filters = {};
      $$("[data-modrinth-filter-key]").forEach(select => {
        const key = select.dataset.modrinthFilterKey;
        if (key) filters[key] = select.value || "";
      });

      $$("[data-modrinth-filter-group]").forEach(group => {
        const key = group.dataset.modrinthFilterGroup;
        if (!key) return;
        filters[key] = Array.from(group.querySelectorAll(".catalog-filter-chip.is-active"))
          .map(button => button.dataset.filterValue)
          .filter(Boolean);
      });

      return filters;
    },

    resetModrinthFilters() {
      const snapshots = $("#modrinthShowSnapshotsCheckbox");
      if (snapshots) snapshots.checked = false;
      this.modrinthFilterOptions = null;
      this.modrinthFilterKey = "";
      this.modrinthSearched = false;
      this.modrinthResults = [];
      this.modrinthLastTotal = 0;
      this.modrinthCurrentPage = 1;
      this.modrinthTotalPages = 1;
      this.renderModrinthResults();
      this.loadModrinthFilters();
      const status = $("#modrinthStatus");
      if (status) {
        status.textContent = this.t("modrinth.filtersReset");
        status.classList.remove("hidden");
      }
    },

    async searchModrinth(event = null, page = null) {
      event?.preventDefault();
      if (page !== null) {
        this.modrinthCurrentPage = Math.max(1, Number(page) || 1);
      }
      const status = $("#modrinthStatus");
      const button = $("#modrinthSearchButton");
      const selected = this.selectedInstanceForCatalog();

      const type = $("#modrinthTypeSelect").value || "mod";

      if (!selected) {
        status.textContent = this.t("modrinth.noInstanceError");
        status.classList.remove("hidden");
        this.modrinthResults = [];
        this.modrinthLastTotal = 0;
        this.modrinthCurrentPage = 1;
        this.modrinthTotalPages = 1;
        this.renderModrinthResults();
        return;
      }

      if (type === "mod" && selected?.loader === "vanilla") {
        status.textContent = this.t("modrinth.vanillaModWarning");
        status.classList.remove("hidden");
        this.modrinthResults = [];
        this.modrinthLastTotal = 0;
        this.modrinthCurrentPage = 1;
        this.modrinthTotalPages = 1;
        this.renderModrinthResults();
        return;
      }

      await this.loadModrinthFilters();

      status.textContent = this.t("modrinth.searching");
      status.classList.remove("hidden");
      button.disabled = true;

      try {
        const limit = this.modrinthPageSize || 24;
        const offset = Math.max(0, (this.modrinthCurrentPage - 1) * limit);
        const result = await window.SLLApi.call("search_modrinth", {
          query: $("#modrinthQueryInput").value.trim(),
          project_type: type,
          index: $("#modrinthSortSelect").value || "relevance",
          instance_id: selected?.id || "",
          filters: this.collectModrinthFilters(),
          limit,
          offset
        });

        if (!result?.ok) {
          status.textContent = this.localizeMessage(result?.error || this.t("error.generic"));
          this.modrinthResults = [];
          this.modrinthLastTotal = 0;
          this.modrinthCurrentPage = 1;
          this.modrinthTotalPages = 1;
          this.renderModrinthResults();
          return;
        }

        this.modrinthSearched = true;
        this.modrinthResults = result.hits || [];
        this.modrinthLastTotal = result.total_hits || this.modrinthResults.length;
        this.modrinthCurrentPage = result.page || this.modrinthCurrentPage || 1;
        this.modrinthTotalPages = result.total_pages || Math.max(1, Math.ceil((this.modrinthLastTotal || 0) / (this.modrinthPageSize || 24)));
        status.textContent = this.t(this.modrinthResults.length ? "modrinth.resultsReady" : "modrinth.noResults");
        this.renderModrinthResults();
      } catch (error) {
        status.textContent = this.localizeMessage(error?.message || String(error));
        this.modrinthResults = [];
        this.modrinthLastTotal = 0;
        this.modrinthCurrentPage = 1;
        this.modrinthTotalPages = 1;
        this.renderModrinthResults();
      } finally {
        button.disabled = false;
      }
    },

    renderModrinthResults() {
      const grid = $("#modrinthResults");
      const empty = $("#modrinthEmpty");
      if (!grid || !empty) return;

      const results = this.modrinthResults || [];
      empty.classList.toggle("hidden", results.length > 0 || !this.modrinthSearched);
      grid.innerHTML = results.map(project => this.modrinthCardHtml(project)).join("");

      $$("[data-modrinth-install]").forEach(button => {
        button.addEventListener("click", () => this.installModrinthProject(button.dataset.modrinthInstall));
      });

      $$("[data-modrinth-open-url]").forEach(button => {
        button.addEventListener("click", () => this.openModrinthProjectUrl(button.dataset.modrinthOpenUrl));
      });

      this.renderModrinthPagination();
    },

    renderModrinthPagination() {
      const box = $("#modrinthPagination");
      if (!box) return;

      const total = Number(this.modrinthLastTotal || 0);
      const pageSize = Number(this.modrinthPageSize || 24);
      const totalPages = Math.max(1, Number(this.modrinthTotalPages || Math.ceil(total / pageSize) || 1));
      const current = Math.max(1, Math.min(totalPages, Number(this.modrinthCurrentPage || 1)));

      if (!this.modrinthSearched || total <= pageSize || totalPages <= 1) {
        box.classList.add("hidden");
        box.innerHTML = "";
        return;
      }

      const pages = this.modrinthVisiblePages(current, totalPages);
      const from = ((current - 1) * pageSize) + 1;
      const to = Math.min(total, current * pageSize);

      box.classList.remove("hidden");
      box.innerHTML = `
        <div class="catalog-pagination__summary">
          ${this.escape(this.t("modrinth.paginationSummary"))
            .replace("{from}", this.formatNumber(from))
            .replace("{to}", this.formatNumber(to))
            .replace("{total}", this.formatNumber(total))}
        </div>
        <div class="catalog-pagination__buttons">
          <button class="catalog-page-btn" type="button" data-modrinth-page="${current - 1}" ${current <= 1 ? "disabled" : ""}>‹</button>
          ${pages.map(item => item === "..."
            ? `<span class="catalog-page-ellipsis">…</span>`
            : `<button class="catalog-page-btn ${item === current ? "is-active" : ""}" type="button" data-modrinth-page="${item}" ${item === current ? "aria-current=\"page\"" : ""}>${item}</button>`
          ).join("")}
          <button class="catalog-page-btn" type="button" data-modrinth-page="${current + 1}" ${current >= totalPages ? "disabled" : ""}>›</button>
        </div>
      `;

      box.querySelectorAll("[data-modrinth-page]").forEach(button => {
        button.addEventListener("click", () => {
          const page = Number(button.dataset.modrinthPage || 1);
          if (page >= 1 && page <= totalPages && page !== current) {
            this.searchModrinth(null, page);
          }
        });
      });
    },

    modrinthVisiblePages(current, totalPages) {
      const result = [];
      const add = value => {
        if (!result.includes(value)) result.push(value);
      };

      add(1);
      for (let page = current - 1; page <= current + 1; page += 1) {
        if (page > 1 && page < totalPages) add(page);
      }
      if (totalPages > 1) add(totalPages);

      const sorted = result.sort((a, b) => a - b);
      const withGaps = [];
      sorted.forEach((page, index) => {
        if (index > 0 && page - sorted[index - 1] > 1) withGaps.push("...");
        withGaps.push(page);
      });
      return withGaps;
    },

    modrinthCardHtml(project) {
      const type = project.project_type || "mod";
      const icon = project.icon_url
        ? `<img src="${this.escape(project.icon_url)}" alt="" loading="lazy">`
        : `<span>${this.escape((project.title || "M").slice(0, 1).toUpperCase())}</span>`;
      const downloads = this.formatNumber(project.downloads || 0);
      const follows = this.formatNumber(project.follows || 0);
      const categories = (project.loaders?.length ? project.loaders : project.categories || [])
        .slice(0, 4)
        .map(item => `<span class="catalog-tag">${this.escape(item)}</span>`)
        .join("");

      const disabled = "";
      const buttonText = type === "modpack" ? this.t("modrinth.installModpack") : this.t("modrinth.install");
      return `
        <article class="catalog-card" data-modrinth-project="${this.escape(project.project_id || project.slug || "")}">
          <div class="catalog-card__icon">${icon}</div>
          <div class="catalog-card__body">
            <div class="catalog-card__top">
              <div>
                <h3>
                  <button class="catalog-card__title-link" type="button" data-modrinth-open-url="${this.escape(project.project_url || "")}" title="${this.escape(this.t("modrinth.openProject"))}">
                    ${this.escape(project.title || project.slug || "Modrinth")}
                  </button>
                </h3>
                <div class="catalog-card__meta">${this.escape(this.modrinthTypeLabel(type))} · ↓ ${downloads} · ★ ${follows}</div>
              </div>
              <span class="catalog-card__type">${this.escape(this.modrinthTypeLabel(type))}</span>
            </div>
            <p>${this.escape(project.description || "")}</p>
            <div class="catalog-tags">${categories}</div>
            <div class="catalog-card__actions">
              <button class="button button--primary button--compact" type="button" data-modrinth-install="${this.escape(project.project_id || project.slug || "")}" ${disabled}>
                ${buttonText}
              </button>
            </div>
          </div>
        </article>
      `;
    },

    async openModrinthProjectUrl(url) {
      if (!url) return;
      try {
        const result = await window.SLLApi.call("open_external_url", url);
        if (!result?.ok) {
          this.toast(result?.error || this.t("error.generic"), true);
        }
      } catch (error) {
        this.toast(error?.message || String(error), true);
      }
    },


    instanceToolText(key) {
      const value = this.t(key);
      if (value && value !== key) return value;

      const lang = window.SLLState?.preferences?.language || "en";
      const fallback = {
        en: {
          "instanceTools.clone": "Clone instance",
          "instanceTools.cloned": "Instance cloned.",
          "instanceTools.clonedNamed": "Instance cloned: {name}"
        },
        uk: {
          "instanceTools.clone": "Клонувати збірку",
          "instanceTools.cloned": "Збірку клоновано.",
          "instanceTools.clonedNamed": "Збірку клоновано: {name}"
        },
        kk: {
          "instanceTools.clone": "Жинақты клондау",
          "instanceTools.cloned": "Жинақ клондалды.",
          "instanceTools.clonedNamed": "Жинақ клондалды: {name}"
        }
      };

      return fallback[lang]?.[key] || fallback.uk?.[key] || fallback.en?.[key] || key;
    },

    deleteInstanceText(key) {
      const value = this.t(key);
      if (value && value !== key) return value;

      const lang = window.SLLState?.preferences?.language || "en";
      const fallback = {
        en: {
          "instanceDelete.eyebrow": "Delete instance",
          "instanceDelete.title": "Delete this instance?",
          "instanceDelete.subtitle": "The launcher entry and the instance folder on disk will be deleted. The official instance can be reinstalled later.",
          "instanceDelete.warning": "This action cannot be undone. Worlds, mods, resource packs, shaders, screenshots and settings inside this instance folder will be removed.",
          "instanceDelete.instance": "Instance",
          "instanceDelete.folder": "Folder",
          "instanceDelete.cancel": "Cancel",
          "instanceDelete.confirm": "Delete instance",
          "instanceDelete.deleted": "Instance deleted. Folder removed from disk.",
          "instanceDelete.deletedMissing": "Instance deleted. Its folder was already missing."
        },
        uk: {
          "instanceDelete.eyebrow": "Видалення збірки",
          "instanceDelete.title": "Видалити цю збірку?",
          "instanceDelete.subtitle": "Запис у лаунчері та папку збірки на диску буде видалено. Офіційну збірку можна буде встановити знову.",
          "instanceDelete.warning": "Цю дію не можна скасувати. Світи, моди, ресурспаки, шейдери, скріншоти й налаштування всередині папки збірки буде видалено.",
          "instanceDelete.instance": "Збірка",
          "instanceDelete.folder": "Папка",
          "instanceDelete.cancel": "Скасувати",
          "instanceDelete.confirm": "Видалити збірку",
          "instanceDelete.deleted": "Збірку видалено. Папку прибрано з диска.",
          "instanceDelete.deletedMissing": "Збірку видалено. Її папка вже була відсутня."
        },
        kk: {
          "instanceDelete.eyebrow": "Жинақты жою",
          "instanceDelete.title": "Бұл жинақты жою керек пе?",
          "instanceDelete.subtitle": "Лаунчердегі жазба және дискідегі жинақ қалтасы жойылады. Ресми жинақты кейін қайта орнатуға болады.",
          "instanceDelete.warning": "Бұл әрекетті қайтару мүмкін емес. Осы жинақ қалтасындағы әлемдер, модтар, ресурспактар, шейдерлер, скриншоттар және баптаулар жойылады.",
          "instanceDelete.instance": "Жинақ",
          "instanceDelete.folder": "Қалта",
          "instanceDelete.cancel": "Бас тарту",
          "instanceDelete.confirm": "Жинақты жою",
          "instanceDelete.deleted": "Жинақ жойылды. Қалта дискіден өшірілді.",
          "instanceDelete.deletedMissing": "Жинақ жойылды. Оның қалтасы бұрыннан жоқ еді."
        }
      };
      return fallback[lang]?.[key] || fallback.uk?.[key] || fallback.en?.[key] || key;
    },

    ensureDeleteInstanceDialogDom() {
      if ($("#deleteInstanceBackdrop")) return;

      const wrapper = document.createElement("div");
      wrapper.innerHTML = `
        <div id="deleteInstanceBackdrop" class="modal-backdrop hidden" aria-hidden="true">
          <section id="deleteInstanceDialog" class="modal-card delete-instance-dialog" role="dialog" aria-modal="true" aria-labelledby="deleteInstanceTitle">
            <header class="modal-card__header">
              <div>
                <div class="eyebrow delete-instance__eyebrow" id="deleteInstanceEyebrow"></div>
                <h2 id="deleteInstanceTitle"></h2>
                <p id="deleteInstanceSubtitle" class="modal-subtitle"></p>
              </div>
              <button id="deleteInstanceClose" class="icon-button" type="button" aria-label="Close">×</button>
            </header>

            <div class="delete-instance__body">
              <div id="deleteInstanceWarning" class="delete-instance__warning"></div>
              <div class="delete-instance__details">
                <div>
                  <span id="deleteInstanceNameLabel"></span>
                  <strong id="deleteInstanceName"></strong>
                </div>
                <div>
                  <span id="deleteInstancePathLabel"></span>
                  <code id="deleteInstancePath"></code>
                </div>
              </div>
            </div>

            <footer class="dependency-preview__actions">
              <button id="deleteInstanceCancel" class="button" type="button"></button>
              <button id="deleteInstanceConfirm" class="button button--danger" type="button"></button>
            </footer>
          </section>
        </div>
      `.trim();

      document.body.appendChild(wrapper.firstElementChild);
    },

    instanceById(instanceId) {
      return (window.SLLState?.instances || []).find(item => item.id === instanceId) || null;
    },

    confirmDeleteInstance(instanceId) {
      this.ensureDeleteInstanceDialogDom();

      return new Promise(resolve => {
        const instance = this.instanceById(instanceId) || {};
        const backdrop = $("#deleteInstanceBackdrop");
        const title = $("#deleteInstanceTitle");
        const subtitle = $("#deleteInstanceSubtitle");
        const eyebrow = $("#deleteInstanceEyebrow");
        const warning = $("#deleteInstanceWarning");
        const nameLabel = $("#deleteInstanceNameLabel");
        const pathLabel = $("#deleteInstancePathLabel");
        const nameValue = $("#deleteInstanceName");
        const pathValue = $("#deleteInstancePath");
        const close = $("#deleteInstanceClose");
        const cancel = $("#deleteInstanceCancel");
        const confirm = $("#deleteInstanceConfirm");

        if (!backdrop || !confirm || !cancel || !close) {
          resolve(false);
          return;
        }

        if (eyebrow) eyebrow.textContent = this.deleteInstanceText("instanceDelete.eyebrow");
        if (title) title.textContent = this.deleteInstanceText("instanceDelete.title");
        if (subtitle) subtitle.textContent = this.deleteInstanceText("instanceDelete.subtitle");
        if (warning) warning.textContent = this.deleteInstanceText("instanceDelete.warning");
        if (nameLabel) nameLabel.textContent = this.deleteInstanceText("instanceDelete.instance");
        if (pathLabel) pathLabel.textContent = this.deleteInstanceText("instanceDelete.folder");
        if (nameValue) nameValue.textContent = instance.name || instanceId || "Instance";
        if (pathValue) pathValue.textContent = instance.game_directory || "data/instances/...";
        cancel.textContent = this.deleteInstanceText("instanceDelete.cancel");
        confirm.textContent = this.deleteInstanceText("instanceDelete.confirm");

        const cleanup = result => {
          backdrop.classList.add("hidden");
          backdrop.setAttribute("aria-hidden", "true");
          close.removeEventListener("click", onCancel);
          cancel.removeEventListener("click", onCancel);
          confirm.removeEventListener("click", onConfirm);
          backdrop.removeEventListener("click", onBackdrop);
          window.removeEventListener("keydown", onKey);
          resolve(result);
        };

        const onConfirm = () => cleanup(true);
        const onCancel = () => cleanup(false);
        const onBackdrop = event => {
          if (event.target === backdrop) cleanup(false);
        };
        const onKey = event => {
          if (event.key === "Escape") cleanup(false);
        };

        close.addEventListener("click", onCancel);
        cancel.addEventListener("click", onCancel);
        confirm.addEventListener("click", onConfirm);
        backdrop.addEventListener("click", onBackdrop);
        window.addEventListener("keydown", onKey);

        backdrop.classList.remove("hidden");
        backdrop.setAttribute("aria-hidden", "false");
        setTimeout(() => confirm.focus(), 30);
      });
    },

    dependencyPreviewText(key) {
      const value = this.t(key);
      if (value && value !== key) return value;

      const lang = window.SLLState?.preferences?.language || "en";
      const fallback = {
        en: {
          "dependencyPreview.eyebrow": "Dependencies",
          "dependencyPreview.title": "Install required dependencies?",
          "dependencyPreview.subtitle": "This project requires additional files.",
          "dependencyPreview.summary": "The launcher will install {count} required dependencies. Already installed: {installed}.",
          "dependencyPreview.conflictSummary": "Some dependency files already exist but do not match the selected source. Installation is blocked to protect user files.",
          "dependencyPreview.mainProject": "Selected project",
          "dependencyPreview.requiredDependencies": "Required dependencies",
          "dependencyPreview.noDependencies": "No required dependencies.",
          "dependencyPreview.willInstall": "Will install",
          "dependencyPreview.alreadyInstalled": "Installed",
          "dependencyPreview.conflict": "Conflict",
          "dependencyPreview.install": "Install",
          "dependencyPreview.installBlocked": "Blocked",
          "dependencyPreview.cancel": "Cancel",
          "dependencyPreview.fallbackConfirm": "This project requires dependencies. Continue installation?"
        },
        uk: {
          "dependencyPreview.eyebrow": "Залежності",
          "dependencyPreview.title": "Встановити обов'язкові залежності?",
          "dependencyPreview.subtitle": "Цей проєкт потребує додаткових файлів.",
          "dependencyPreview.summary": "Лаунчер встановить обов'язкові залежності: {count}. Уже встановлено: {installed}.",
          "dependencyPreview.conflictSummary": "Деякі файли залежностей уже існують, але не збігаються з вибраним джерелом. Встановлення заблоковано, щоб не перезаписати файли користувача.",
          "dependencyPreview.mainProject": "Вибраний проєкт",
          "dependencyPreview.requiredDependencies": "Обов'язкові залежності",
          "dependencyPreview.noDependencies": "Обов'язкових залежностей немає.",
          "dependencyPreview.willInstall": "Буде встановлено",
          "dependencyPreview.alreadyInstalled": "Встановлено",
          "dependencyPreview.conflict": "Конфлікт",
          "dependencyPreview.install": "Встановити",
          "dependencyPreview.installBlocked": "Заблоковано",
          "dependencyPreview.cancel": "Скасувати",
          "dependencyPreview.fallbackConfirm": "Цей проєкт потребує залежностей. Продовжити встановлення?"
        },
        kk: {
          "dependencyPreview.eyebrow": "Тәуелділіктер",
          "dependencyPreview.title": "Міндетті тәуелділіктерді орнату керек пе?",
          "dependencyPreview.subtitle": "Бұл жоба қосымша файлдарды қажет етеді.",
          "dependencyPreview.summary": "Лаунчер {count} міндетті тәуелділікті орнатады. Бұрын орнатылған: {installed}.",
          "dependencyPreview.conflictSummary": "Кейбір тәуелділік файлдары бұрыннан бар, бірақ таңдалған дереккөзге сәйкес келмейді. Пайдаланушы файлдарын қорғау үшін орнату бұғатталды.",
          "dependencyPreview.mainProject": "Таңдалған жоба",
          "dependencyPreview.requiredDependencies": "Міндетті тәуелділіктер",
          "dependencyPreview.noDependencies": "Міндетті тәуелділіктер жоқ.",
          "dependencyPreview.willInstall": "Орнатылады",
          "dependencyPreview.alreadyInstalled": "Орнатылған",
          "dependencyPreview.conflict": "Қақтығыс",
          "dependencyPreview.install": "Орнату",
          "dependencyPreview.installBlocked": "Бұғатталған",
          "dependencyPreview.cancel": "Бас тарту",
          "dependencyPreview.fallbackConfirm": "Бұл жоба тәуелділіктерді қажет етеді. Орнатуды жалғастыру керек пе?"
        }
      };
      return fallback[lang]?.[key] || fallback.uk?.[key] || fallback.en?.[key] || key;
    },

    ensureDependencyPreviewDom() {
      if ($("#dependencyPreviewBackdrop")) return;

      const wrapper = document.createElement("div");
      wrapper.innerHTML = `
        <div id="dependencyPreviewBackdrop" class="modal-backdrop hidden" aria-hidden="true">
          <section id="dependencyPreviewDialog" class="modal-card dependency-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="dependencyPreviewTitle">
            <header class="modal-card__header">
              <div>
                <div class="eyebrow" id="dependencyPreviewEyebrow"></div>
                <h2 id="dependencyPreviewTitle"></h2>
                <p id="dependencyPreviewSubtitle" class="modal-subtitle"></p>
              </div>
              <button id="dependencyPreviewClose" class="icon-button" type="button" aria-label="Close">×</button>
            </header>

            <div class="dependency-preview">
              <div id="dependencyPreviewSummary" class="form-note"></div>
              <div id="dependencyPreviewMain" class="dependency-preview__main"></div>
              <div id="dependencyPreviewList" class="dependency-preview__list"></div>
            </div>

            <footer class="dependency-preview__actions">
              <button id="dependencyPreviewCancel" class="button" type="button"></button>
              <button id="dependencyPreviewInstall" class="button button--primary" type="button"></button>
            </footer>
          </section>
        </div>
      `.trim();

      document.body.appendChild(wrapper.firstElementChild);
    },

    dependencyPreviewItemHtml(item, badgeText = "") {
      const title = item.title || item.project_id || item.filename || "Dependency";
      const version = item.version_number ? ` · ${item.version_number}` : "";
      const meta = `${item.filename || ""}${version ? `<br>${this.escape(version.replace(/^ · /, ""))}` : ""}`;
      const badgeClass = item.conflict
        ? "dependency-preview__badge--danger"
        : item.already_installed
          ? "dependency-preview__badge--ok"
          : "";
      return `
        <div class="dependency-preview__item">
          <div>
            <div class="dependency-preview__item-title">${this.escape(title)}</div>
            <div class="dependency-preview__item-meta">${meta}</div>
          </div>
          <span class="dependency-preview__badge ${badgeClass}">${this.escape(badgeText)}</span>
        </div>
      `;
    },

    showDependencyPreview(plan) {
      this.ensureDependencyPreviewDom();
      return new Promise(resolve => {
        const backdrop = $("#dependencyPreviewBackdrop");
        const summary = $("#dependencyPreviewSummary");
        const main = $("#dependencyPreviewMain");
        const list = $("#dependencyPreviewList");
        const install = $("#dependencyPreviewInstall");
        const cancel = $("#dependencyPreviewCancel");
        const closeButton = $("#dependencyPreviewClose");
        const title = $("#dependencyPreviewTitle");
        const subtitle = $("#dependencyPreviewSubtitle");
        const eyebrow = $("#dependencyPreviewEyebrow");

        if (!backdrop || !summary || !main || !list || !install || !cancel || !closeButton) {
          resolve(window.confirm(this.dependencyPreviewText("dependencyPreview.fallbackConfirm")));
          return;
        }

        if (eyebrow) eyebrow.textContent = this.dependencyPreviewText("dependencyPreview.eyebrow");
        cancel.textContent = this.dependencyPreviewText("dependencyPreview.cancel");

        const deps = plan.dependencies || [];
        const depsToInstall = plan.dependencies_to_install || [];
        const depsInstalled = plan.dependencies_already_installed || [];
        const conflicts = plan.conflicts || [];
        const sourceLabel = plan.source === "curseforge" ? "CurseForge" : "Modrinth";
        const hasConflicts = conflicts.length > 0;

        title.textContent = this.dependencyPreviewText("dependencyPreview.title");
        subtitle.textContent = `${sourceLabel} · ${this.dependencyPreviewText("dependencyPreview.subtitle")}`;

        summary.textContent = hasConflicts
          ? this.dependencyPreviewText("dependencyPreview.conflictSummary")
          : this.dependencyPreviewText("dependencyPreview.summary")
              .replace("{count}", String(depsToInstall.length))
              .replace("{installed}", String(depsInstalled.length));

        main.innerHTML = `
          <div class="dependency-preview__section-title">${this.escape(this.dependencyPreviewText("dependencyPreview.mainProject"))}</div>
          ${this.dependencyPreviewItemHtml(plan.main || {}, plan.main?.already_installed ? this.dependencyPreviewText("dependencyPreview.alreadyInstalled") : this.dependencyPreviewText("dependencyPreview.willInstall"))}
        `;

        if (!deps.length) {
          list.innerHTML = `<div class="form-note">${this.escape(this.dependencyPreviewText("dependencyPreview.noDependencies"))}</div>`;
        } else {
          list.innerHTML = `
            <div class="dependency-preview__section-title">${this.escape(this.dependencyPreviewText("dependencyPreview.requiredDependencies"))}</div>
            ${deps.map(item => this.dependencyPreviewItemHtml(
              item,
              item.conflict
                ? this.dependencyPreviewText("dependencyPreview.conflict")
                : item.already_installed
                  ? this.dependencyPreviewText("dependencyPreview.alreadyInstalled")
                  : this.dependencyPreviewText("dependencyPreview.willInstall")
            )).join("")}
          `;
        }

        install.disabled = hasConflicts;
        install.textContent = hasConflicts ? this.dependencyPreviewText("dependencyPreview.installBlocked") : this.dependencyPreviewText("dependencyPreview.install");

        const cleanup = result => {
          backdrop.classList.add("hidden");
          backdrop.setAttribute("aria-hidden", "true");
          install.removeEventListener("click", onInstall);
          cancel.removeEventListener("click", onCancel);
          closeButton.removeEventListener("click", onCancel);
          backdrop.removeEventListener("click", onBackdrop);
          window.removeEventListener("keydown", onKey);
          resolve(result);
        };

        const onInstall = () => cleanup(true);
        const onCancel = () => cleanup(false);
        const onBackdrop = event => {
          if (event.target === backdrop) cleanup(false);
        };
        const onKey = event => {
          if (event.key === "Escape") cleanup(false);
        };

        install.addEventListener("click", onInstall);
        cancel.addEventListener("click", onCancel);
        closeButton.addEventListener("click", onCancel);
        backdrop.addEventListener("click", onBackdrop);
        window.addEventListener("keydown", onKey);

        backdrop.classList.remove("hidden");
        backdrop.setAttribute("aria-hidden", "false");
        setTimeout(() => (hasConflicts ? cancel : install).focus(), 30);
      });
    },

    async confirmDependencyPlan(apiMethod, payload) {
      const plan = await window.SLLApi.call(apiMethod, payload);
      if (!plan?.ok) {
        this.toast(this.localizeMessage(plan?.error || this.t("error.generic")), true);
        return false;
      }
      if (!plan.requires_confirmation) return true;
      return await this.showDependencyPreview(plan);
    },

    async installModrinthProject(projectId) {
      const selected = this.selectedInstanceForCatalog();

      const project = (this.modrinthResults || []).find(item => (item.project_id || item.slug) === projectId);
      if (!project) {
        this.toast(this.t("modrinth.projectMissing"), true);
        return;
      }

      const buttons = $$(`[data-modrinth-install="${CSS.escape(projectId)}"]`);
      buttons.forEach(button => {
        button.disabled = true;
        button.textContent = this.t("modrinth.installing");
      });

      try {
        if (!selected) {
          this.toast(this.t("modrinth.noInstanceError"), true);
          return;
        }

        const payload = {
          instance_id: selected?.id || "",
          project_id: projectId,
          project_type: project.project_type,
          filters: this.collectModrinthFilters()
        };

        const confirmed = await this.confirmDependencyPlan("preview_modrinth_install", payload);
        if (!confirmed) return;

        const result = await window.SLLApi.call("install_modrinth_project", payload);

        if (!result?.ok) {
          this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
          return;
        }

        if (result.state) this.setState(result.state);

        const isModpack = project.project_type === "modpack";
        const dependencyCount = Array.isArray(result.dependencies_installed) ? result.dependencies_installed.length : 0;
        const dependencySuffix = dependencyCount > 0
          ? ` (+${dependencyCount} ${this.t("modrinth.dependencies")})`
          : "";
        const installLabel = result.already_installed ? this.t("modrinth.alreadyInstalled") : this.t("modrinth.installed");
        const message = isModpack
          ? `${this.t("modrinth.modpackInstalledInto")}: ${selected.name}`
          : `${installLabel}: ${result.filename || project.title}${dependencySuffix}`;
        this.toast(message);

        const logTarget = isModpack
          ? `${this.t("modrinth.target")} ${selected.name}`
          : `${result.folder || ""}/${result.filename || ""}`;
        this.appendLog(`${installLabel} ${project.title} → ${logTarget}${dependencySuffix}`);

        if (selected && this.instanceWindowId === selected.id) {
          const refreshed = await window.SLLApi.call("get_instance_window_data", selected.id);
          if (refreshed?.ok) this.renderInstanceWindow(refreshed);
        }
      } catch (error) {
        this.toast(error?.message || String(error), true);
      } finally {
        buttons.forEach(button => {
          button.disabled = false;
          button.textContent = project?.project_type === "modpack" ? this.t("modrinth.installModpack") : this.t("modrinth.install");
        });
      }
    },


    curseforgeTypeLabel(type) {
      const key = {
        mod: "curseforge.mod",
        resourcepack: "curseforge.resourcepack",
        shader: "curseforge.shader",
        modpack: "curseforge.modpack"
      }[type] || "curseforge.project";
      return this.t(key);
    },

    currentCurseForgeFilterKey(selected = null, type = null, includeSnapshots = null) {
      selected = selected || this.selectedInstanceForCatalog();
      type = type || $("#curseforgeTypeSelect")?.value || "mod";
      includeSnapshots = includeSnapshots ?? Boolean($("#curseforgeShowSnapshotsCheckbox")?.checked);
      return `${selected?.id || ""}|${type}|${includeSnapshots}`;
    },

    async loadCurseForgeFilters() {
      const selected = this.selectedInstanceForCatalog();
      const type = $("#curseforgeTypeSelect")?.value || "mod";
      const includeSnapshots = Boolean($("#curseforgeShowSnapshotsCheckbox")?.checked);
      const key = this.currentCurseForgeFilterKey(selected, type, includeSnapshots);

      if (!selected) {
        this.curseforgeFilterOptions = null;
        this.curseforgeFilterKey = "";
        this.renderCurseForgeFilters();
        return null;
      }

      if (this.curseforgeFilterOptions && this.curseforgeFilterKey === key) {
        this.renderCurseForgeFilters();
        return this.curseforgeFilterOptions;
      }

      if (this.curseforgeFilterLoading) return this.curseforgeFilterOptions;

      this.curseforgeFilterLoading = true;
      this.renderCurseForgeFilters();

      try {
        const result = await window.SLLApi.call("get_curseforge_filter_options", {
          project_type: type,
          instance_id: selected.id,
          include_snapshots: includeSnapshots
        });

        if (result?.ok) {
          this.curseforgeFilterOptions = result;
          this.curseforgeFilterKey = key;
        } else {
          this.curseforgeFilterOptions = null;
          this.curseforgeFilterKey = "";
        }
      } catch (_error) {
        this.curseforgeFilterOptions = null;
        this.curseforgeFilterKey = "";
      } finally {
        this.curseforgeFilterLoading = false;
        this.renderCurseForgeFilters();
      }

      return this.curseforgeFilterOptions;
    },

    renderCurseForgeFilters() {
      const box = $("#curseforgeFilters");
      const fields = $("#curseforgeFilterFields");
      const groups = $("#curseforgeFilterGroups");
      if (!box || !fields || !groups) return;

      const options = this.curseforgeFilterOptions;
      if (!options?.ok) {
        box.classList.add("hidden");
        fields.innerHTML = "";
        groups.innerHTML = "";
        return;
      }

      const currentKey = this.currentCurseForgeFilterKey();
      const preserveCurrentValues = this.curseforgeRenderedFilterKey === currentKey;
      const previousFilters = preserveCurrentValues ? this.collectCurseForgeFilters() : {};

      box.classList.remove("hidden");
      const sections = options.sections || [];
      const selectSections = sections.filter(section => section.control === "select");
      const chipSections = sections.filter(section => section.control === "chips" && (section.choices || []).length);

      fields.innerHTML = selectSections.map(section =>
        this.curseforgeSelectFilterHtml(section, previousFilters[section.key])
      ).join("");
      groups.innerHTML = chipSections.map(section =>
        this.curseforgeChipFilterHtml(section, previousFilters[section.key] || [])
      ).join("");

      this.curseforgeRenderedFilterKey = currentKey;

      fields.querySelectorAll("select[data-curseforge-filter-key]").forEach(select => {
        select.addEventListener("change", () => {
          if (this.curseforgeSearched) this.searchCurseForge(null, 1);
        });
      });

      groups.querySelectorAll("[data-curseforge-filter-chip]").forEach(button => {
        button.addEventListener("click", () => {
          button.classList.toggle("is-active");
          if (this.curseforgeSearched) this.searchCurseForge(null, 1);
        });
      });
    },

    curseforgeFilterLabel(key) {
      return this.t(`curseforge.filter.${key}`);
    },

    curseforgeFilterChoiceLabel(sectionKey, choice) {
      const id = String(choice?.id || "").trim();
      const raw = String(choice?.label || id).trim();
      if (sectionKey === "category_ids") {
        return this.curseforgeCategoryLabel(choice);
      }
      const lang = window.SLLState?.preferences?.language || "en";
      const labels = this.curseforgeChoiceLabels();
      return labels[lang]?.[id] || labels.en?.[id] || raw;
    },

    curseforgeSelectFilterHtml(section, selectedValue = null) {
      const choices = section.choices || [];
      const choiceIds = new Set(choices.map(choice => String(choice.id)));
      const savedValue = selectedValue == null ? "" : String(selectedValue);
      const defaultValue = savedValue && choiceIds.has(savedValue) ? savedValue : (section.default || "");
      return `
        <label class="form-field catalog-filter-field">
          <span>${this.escape(this.curseforgeFilterLabel(section.key))}</span>
          <select class="select" data-curseforge-filter-key="${this.escape(section.key)}">
            ${choices.map(choice => {
              const id = String(choice.id);
              return `
                <option value="${this.escape(id)}" ${id === String(defaultValue) ? "selected" : ""}>${this.escape(this.curseforgeFilterChoiceLabel(section.key, choice))}</option>
              `;
            }).join("")}
          </select>
        </label>
      `;
    },

    curseforgeChipFilterHtml(section, selectedValues = []) {
      const choices = section.choices || [];
      const active = new Set((Array.isArray(selectedValues) ? selectedValues : [])
        .map(value => String(value))
        .filter(Boolean));
      return `
        <section class="catalog-filter-group" data-curseforge-filter-group="${this.escape(section.key)}">
          <div class="catalog-filter-group__title">${this.escape(this.curseforgeFilterLabel(section.key))}</div>
          <div class="catalog-filter-chips">
            ${choices.map(choice => {
              const id = String(choice.id);
              return `
                <button class="catalog-filter-chip ${active.has(id) ? "is-active" : ""}" type="button" data-curseforge-filter-chip="${this.escape(section.key)}" data-filter-value="${this.escape(id)}" data-filter-slug="${this.escape(choice.slug || "")}">
                  ${this.escape(this.curseforgeFilterChoiceLabel(section.key, choice))}
                </button>
              `;
            }).join("")}
          </div>
        </section>
      `;
    },

    collectCurseForgeFilters() {
      const filters = {};
      $$("[data-curseforge-filter-key]").forEach(select => {
        const key = select.dataset.curseforgeFilterKey;
        if (key) filters[key] = select.value || "";
      });

      $$("[data-curseforge-filter-group]").forEach(group => {
        const key = group.dataset.curseforgeFilterGroup;
        if (!key) return;
        filters[key] = Array.from(group.querySelectorAll(".catalog-filter-chip.is-active"))
          .map(button => button.dataset.filterValue)
          .filter(Boolean);
      });

      return filters;
    },

    resetCurseForgeFilters() {
      const snapshots = $("#curseforgeShowSnapshotsCheckbox");
      if (snapshots) snapshots.checked = false;
      const manualOnly = $("#curseforgeShowManualOnlyCheckbox");
      if (manualOnly) manualOnly.checked = true;
      this.curseforgeFilterOptions = null;
      this.curseforgeFilterKey = "";
      this.curseforgeRenderedFilterKey = "";
      const fields = $("#curseforgeFilterFields");
      const groups = $("#curseforgeFilterGroups");
      if (fields) fields.innerHTML = "";
      if (groups) groups.innerHTML = "";
      this.curseforgeSearched = false;
      this.curseforgeResults = [];
      this.curseforgeLastTotal = 0;
      this.curseforgeCurrentPage = 1;
      this.curseforgeTotalPages = 1;
      this.renderCurseForgeResults();
      this.loadCurseForgeFilters();
      const status = $("#curseforgeStatus");
      if (status) {
        status.textContent = this.t("curseforge.filtersReset");
        status.classList.remove("hidden");
      }
    },

    curseforgeCategoryLabel(category) {
      const rawName = typeof category === "string" ? category : (category?.label || category?.name || category?.slug || "");
      const rawSlug = typeof category === "object" ? (category.slug || "") : "";
      const key = this.curseforgeCategoryKey(rawSlug || rawName);
      const language = window.SLLState.preferences?.language || "en";
      const maps = this.curseforgeChoiceLabels();
      return maps[language]?.[key] || maps.en?.[key] || rawName;
    },

    curseforgeCategoryKey(value) {
      return String(value || "")
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/\+/g, " plus ")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
    },

    curseforgeChoiceLabels() {
      return {
        en: {
          "": "Any",
          fabric: "Fabric",
          forge: "Forge",
          quilt: "Quilt",
          neoforge: "NeoForge",
          "adventure-and-rpg": "Adventure and RPG",
          adventure: "Adventure",
          "armor-weapons-and-tools": "Armor, Weapons and Tools",
          "cosmetic": "Cosmetic",
          "cosmetic-armor": "Cosmetic armor",
          "food": "Food",
          "magic": "Magic",
          "mobs": "Mobs",
          "technology": "Technology",
          "technology-processing": "Processing",
          "technology-player-transport": "Player transport",
          "technology-energy": "Energy",
          "utility-and-qol": "Utility and QoL",
          "map-and-information": "Map and information",
          "world-gen": "World generation",
          "worldgen": "World generation",
          "biomes": "Biomes",
          "storage": "Storage",
          "transport": "Transport",
          "farming": "Farming",
          "energy": "Energy",
          "library-api": "Library/API",
          "api-and-library": "API and Library",
          "automation": "Automation",
          "structures": "Structures",
          "dimensions": "Dimensions",
          "ores-and-resources": "Ores and resources",
          "server-utility": "Server utility",
          "miscellaneous": "Miscellaneous",
          "mc-addons": "Addons",
          "bug-fixes": "Bug fixes",
          "commands": "Commands",
          "equipment": "Equipment",
          "genetics": "Genetics",
          "redstone": "Redstone",
          "twitch-integration": "Twitch integration",
          "16x": "16x",
          "32x": "32x",
          "64x": "64x",
          "128x": "128x",
          "256x": "256x",
          "512x-and-higher": "512x and higher",
          "animated": "Animated",
          "audio": "Audio",
          "font-packs": "Fonts",
          "medieval": "Medieval",
          "modern": "Modern",
          "mod-support": "Mod support",
          "photo-realistic": "Photo realistic",
          "traditional": "Traditional",
          "realistic": "Realistic",
          "semi-realistic": "Semi-realistic",
          "fantasy": "Fantasy",
          "vanilla-plus": "Vanilla+",
          "low-end": "Low-end",
          "high-end": "High-end",
          "pbr": "PBR",
          "path-tracing": "Path tracing"
        },
        uk: {
          "": "Будь-який",
          fabric: "Fabric",
          forge: "Forge",
          quilt: "Quilt",
          neoforge: "NeoForge",
          "adventure-and-rpg": "Пригоди та RPG",
          adventure: "Пригоди",
          "armor-weapons-and-tools": "Броня, зброя та інструменти",
          "cosmetic": "Косметика",
          "cosmetic-armor": "Косметична броня",
          "food": "Їжа",
          "magic": "Магія",
          "mobs": "Моби",
          "technology": "Технології",
          "technology-processing": "Обробка",
          "technology-player-transport": "Транспорт гравця",
          "technology-energy": "Енергія",
          "utility-and-qol": "Корисне та QoL",
          "map-and-information": "Мапа та інформація",
          "world-gen": "Генерація світу",
          "worldgen": "Генерація світу",
          "biomes": "Біоми",
          "storage": "Сховища",
          "transport": "Транспорт",
          "farming": "Фермерство",
          "energy": "Енергія",
          "library-api": "Бібліотека/API",
          "api-and-library": "API та бібліотеки",
          "automation": "Автоматизація",
          "structures": "Структури",
          "dimensions": "Виміри",
          "ores-and-resources": "Руди та ресурси",
          "server-utility": "Серверні утиліти",
          "miscellaneous": "Різне",
          "mc-addons": "Аддони",
          "bug-fixes": "Виправлення помилок",
          "commands": "Команди",
          "equipment": "Спорядження",
          "genetics": "Генетика",
          "redstone": "Редстоун",
          "twitch-integration": "Інтеграція Twitch",
          "animated": "Анімовані",
          "audio": "Аудіо",
          "font-packs": "Шрифти",
          "medieval": "Середньовічні",
          "modern": "Сучасні",
          "mod-support": "Підтримка модів",
          "photo-realistic": "Фотореалістичні",
          "traditional": "Традиційні",
          "realistic": "Реалістичні",
          "semi-realistic": "Напівреалістичні",
          "fantasy": "Фентезі",
          "vanilla-plus": "Vanilla+",
          "low-end": "Для слабких ПК",
          "high-end": "Для потужних ПК",
          "path-tracing": "Path tracing"
        },
        kk: {
          "": "Кез келген",
          fabric: "Fabric",
          forge: "Forge",
          quilt: "Quilt",
          neoforge: "NeoForge",
          "adventure-and-rpg": "Шытырман оқиға және RPG",
          adventure: "Шытырман оқиға",
          "armor-weapons-and-tools": "Сауыт, қару және құралдар",
          "cosmetic": "Косметика",
          "cosmetic-armor": "Косметикалық сауыт",
          "food": "Тағам",
          "magic": "Магия",
          "mobs": "Мобтар",
          "technology": "Технология",
          "technology-processing": "Өңдеу",
          "technology-player-transport": "Ойыншы көлігі",
          "technology-energy": "Энергия",
          "utility-and-qol": "Пайдалы және QoL",
          "map-and-information": "Карта және ақпарат",
          "world-gen": "Әлем генерациясы",
          "worldgen": "Әлем генерациясы",
          "biomes": "Биомдар",
          "storage": "Сақтау",
          "transport": "Көлік",
          "farming": "Фермерлік",
          "energy": "Энергия",
          "library-api": "Кітапхана/API",
          "api-and-library": "API және кітапхана",
          "automation": "Автоматтандыру",
          "structures": "Құрылымдар",
          "dimensions": "Өлшемдер",
          "ores-and-resources": "Кендер мен ресурстар",
          "server-utility": "Сервер утилиталары",
          "miscellaneous": "Әртүрлі",
          "mc-addons": "Аддондар",
          "bug-fixes": "Қате түзетулері",
          "commands": "Командалар",
          "equipment": "Жабдық",
          "genetics": "Генетика",
          "redstone": "Редстоун",
          "twitch-integration": "Twitch интеграциясы",
          "animated": "Анимацияланған",
          "audio": "Аудио",
          "font-packs": "Қаріптер",
          "medieval": "Ортағасырлық",
          "modern": "Заманауи",
          "mod-support": "Мод қолдауы",
          "photo-realistic": "Фотореалистік",
          "traditional": "Дәстүрлі",
          "realistic": "Реалистік",
          "semi-realistic": "Жартылай реалистік",
          "fantasy": "Фэнтези",
          "vanilla-plus": "Vanilla+",
          "low-end": "Әлсіз ПК үшін",
          "high-end": "Қуатты ПК үшін",
          "path-tracing": "Path tracing"
        }
      };
    },

    renderCurseForge() {
      const selected = this.selectedInstanceForCatalog();
      const info = $("#curseforgeSelectedInstance");
      if (info) {
        if (selected) {
          const loader = selected.loader === "vanilla" ? "Vanilla" : this.capitalize(selected.loader || "");
          info.innerHTML = `
            <span>${this.t("curseforge.target")}</span>
            <strong>${this.escape(selected.name)} · ${this.escape(selected.minecraft_version || "?")} · ${this.escape(loader)}</strong>
          `;
        } else {
          info.innerHTML = `<span>${this.t("curseforge.noTarget")}</span>`;
        }
      }

      const type = $("#curseforgeTypeSelect")?.value || "mod";
      this.loadCurseForgeFilters();
      const status = $("#curseforgeStatus");
      if (status && type === "mod" && selected?.loader === "vanilla") {
        status.textContent = this.t("curseforge.vanillaModWarning");
        status.classList.remove("hidden");
      } else if (status && !this.curseforgeSearched) {
        status.textContent = this.curseforgeCatalogHint(type);
        status.classList.remove("hidden");
      }

      this.renderCurseForgeResults();
    },

    async searchCurseForge(event = null, page = null) {
      event?.preventDefault();
      if (page !== null) {
        this.curseforgeCurrentPage = Math.max(1, Number(page) || 1);
      }

      const status = $("#curseforgeStatus");
      const button = $("#curseforgeSearchButton");
      const selected = this.selectedInstanceForCatalog();
      const type = $("#curseforgeTypeSelect")?.value || "mod";

      if (!selected) {
        status.textContent = this.t("curseforge.noInstanceError");
        status.classList.remove("hidden");
        this.curseforgeResults = [];
        this.curseforgeLastTotal = 0;
        this.curseforgeCurrentPage = 1;
        this.curseforgeTotalPages = 1;
        this.renderCurseForgeResults();
        return;
      }

      if (type === "mod" && selected?.loader === "vanilla") {
        status.textContent = this.t("curseforge.vanillaModWarning");
        status.classList.remove("hidden");
        this.curseforgeResults = [];
        this.curseforgeLastTotal = 0;
        this.curseforgeCurrentPage = 1;
        this.curseforgeTotalPages = 1;
        this.renderCurseForgeResults();
        return;
      }

      await this.loadCurseForgeFilters();

      status.textContent = this.t("curseforge.searching");
      status.classList.remove("hidden");
      if (button) button.disabled = true;

      try {
        const query = $("#curseforgeQueryInput")?.value.trim() || "";
        const sort = $("#curseforgeSortSelect")?.value || "popular";
        const showManualOnly = $("#curseforgeShowManualOnlyCheckbox")?.checked !== false;
        const filters = this.collectCurseForgeFilters();
        const gameVersion = filters.game_version || selected?.minecraft_version || "";
        const loader = ["mod", "modpack"].includes(type) ? (filters.loader || selected?.loader || "") : "";
        const categoryIds = Array.isArray(filters.category_ids) ? filters.category_ids : [];

        const limit = this.curseforgePageSize || 24;
        const offset = Math.max(0, (this.curseforgeCurrentPage - 1) * limit);
        const result = await window.SLLApi.call("search_curseforge", {
          query,
          project_type: type,
          index: sort,
          show_manual_only: showManualOnly,
          instance_id: selected?.id || "",
          filters: {
            game_version: gameVersion,
            loader,
            category_ids: categoryIds
          },
          limit,
          offset
        });

        if (!result?.ok) {
          status.textContent = this.localizeMessage(result?.error || this.t("error.generic"));
          this.curseforgeResults = [];
          this.curseforgeLastTotal = 0;
          this.curseforgeCurrentPage = 1;
          this.curseforgeTotalPages = 1;
          this.renderCurseForgeResults();
          return;
        }

        this.curseforgeSearched = true;
        this.curseforgeResults = result.hits || [];
        this.curseforgeLastTotal = result.total_hits || this.curseforgeResults.length;
        this.curseforgeCurrentPage = result.page || this.curseforgeCurrentPage || 1;
        this.curseforgeTotalPages = result.total_pages || Math.max(1, Math.ceil((this.curseforgeLastTotal || 0) / (this.curseforgePageSize || 24)));
        status.textContent = this.t(this.curseforgeResults.length ? "curseforge.resultsReady" : "curseforge.noResults");
        this.renderCurseForgeResults();
      } catch (error) {
        status.textContent = this.localizeMessage(error?.message || String(error));
        this.curseforgeResults = [];
        this.curseforgeLastTotal = 0;
        this.curseforgeCurrentPage = 1;
        this.curseforgeTotalPages = 1;
        this.renderCurseForgeResults();
      } finally {
        if (button) button.disabled = false;
      }
    },

    renderCurseForgeResults() {
      const grid = $("#curseforgeResults");
      const empty = $("#curseforgeEmpty");
      if (!grid || !empty) return;

      const results = this.curseforgeResults || [];
      empty.classList.toggle("hidden", results.length > 0 || !this.curseforgeSearched);
      grid.innerHTML = results.map(project => this.curseforgeCardHtml(project)).join("");

      $$('[data-curseforge-install]').forEach(button => {
        button.addEventListener("click", () => this.installCurseForgeProject(button.dataset.curseforgeInstall));
      });

      $$('[data-curseforge-open-url]').forEach(button => {
        button.addEventListener("click", () => this.openCurseForgeProjectUrl(button.dataset.curseforgeOpenUrl));
      });

      this.renderCurseForgePagination();
    },

    renderCurseForgePagination() {
      const box = $("#curseforgePagination");
      if (!box) return;

      const total = Number(this.curseforgeLastTotal || 0);
      const pageSize = Number(this.curseforgePageSize || 24);
      const totalPages = Math.max(1, Number(this.curseforgeTotalPages || Math.ceil(total / pageSize) || 1));
      const current = Math.max(1, Math.min(totalPages, Number(this.curseforgeCurrentPage || 1)));

      if (!this.curseforgeSearched || total <= pageSize || totalPages <= 1) {
        box.classList.add("hidden");
        box.innerHTML = "";
        return;
      }

      const pages = this.modrinthVisiblePages(current, totalPages);
      const from = ((current - 1) * pageSize) + 1;
      const to = Math.min(total, current * pageSize);

      box.classList.remove("hidden");
      box.innerHTML = `
        <div class="catalog-pagination__summary">
          ${this.escape(this.t("curseforge.paginationSummary"))
            .replace("{from}", this.formatNumber(from))
            .replace("{to}", this.formatNumber(to))
            .replace("{total}", this.formatNumber(total))}
        </div>
        <div class="catalog-pagination__buttons">
          <button class="catalog-page-btn" type="button" data-curseforge-page="${current - 1}" ${current <= 1 ? "disabled" : ""}>‹</button>
          ${pages.map(item => item === "..."
            ? `<span class="catalog-page-ellipsis">…</span>`
            : `<button class="catalog-page-btn ${item === current ? "is-active" : ""}" type="button" data-curseforge-page="${item}" ${item === current ? "aria-current=\"page\"" : ""}>${item}</button>`
          ).join("")}
          <button class="catalog-page-btn" type="button" data-curseforge-page="${current + 1}" ${current >= totalPages ? "disabled" : ""}>›</button>
        </div>
      `;

      box.querySelectorAll("[data-curseforge-page]").forEach(button => {
        button.addEventListener("click", () => {
          const page = Number(button.dataset.curseforgePage || 1);
          if (page >= 1 && page <= totalPages && page !== current) {
            this.searchCurseForge(null, page);
          }
        });
      });
    },

    curseforgeCardHtml(project) {
      const type = project.project_type || "mod";
      const projectId = String(project.project_id || project.slug || "");
      const icon = project.icon_url
        ? `<img src="${this.escape(project.icon_url)}" alt="" loading="lazy">`
        : `<span>${this.escape((project.title || "C").slice(0, 1).toUpperCase())}</span>`;
      const downloads = this.formatNumber(project.downloads || 0);
      const tags = [
        ...(project.loaders || []).map(item => this.capitalize(String(item))),
        ...(project.game_versions || []),
        ...(project.categories || []).map(item => this.curseforgeCategoryLabel(item))
      ].filter(Boolean).slice(0, 5)
        .map(item => `<span class="catalog-tag">${this.escape(item)}</span>`)
        .join("");

      const isModpack = type === "modpack";
      const downloadAvailable = project.compatible_file?.download_available !== false;
      const buttonText = isModpack
        ? this.t("curseforge.install")
        : downloadAvailable
          ? this.t("curseforge.install")
          : this.t("curseforge.downloadUnavailableShort");
      const disabled = (!downloadAvailable) ? "disabled" : "";
      const title = isModpack
        ? this.t("curseforge.installModpackHint")
        : downloadAvailable
          ? this.t("curseforge.install")
          : this.t("curseforge.downloadUnavailableHint");

      return `
        <article class="catalog-card" data-curseforge-project="${this.escape(projectId)}">
          <div class="catalog-card__icon">${icon}</div>
          <div class="catalog-card__body">
            <div class="catalog-card__top">
              <div>
                <h3>
                  <button class="catalog-card__title-link" type="button" data-curseforge-open-url="${this.escape(project.project_url || "")}" title="${this.escape(this.t("curseforge.openProject"))}">
                    ${this.escape(project.title || project.slug || "CurseForge")}
                  </button>
                </h3>
                <div class="catalog-card__meta">${this.escape(this.curseforgeTypeLabel(type))} · ↓ ${downloads}${project.compatible_file?.file_name ? ` · ${this.escape(project.compatible_file.file_name)}` : ""}</div>
              </div>
              <span class="catalog-card__type">${this.escape(this.curseforgeTypeLabel(type))}</span>
            </div>
            <p>${this.escape(project.description || "")}</p>
            <div class="catalog-tags">${tags}</div>
            <div class="catalog-card__actions">
              <button class="button button--primary button--compact" type="button" data-curseforge-install="${this.escape(projectId)}" title="${this.escape(title)}" ${disabled}>
                ${buttonText}
              </button>
            </div>
          </div>
        </article>
      `;
    },

    async openCurseForgeProjectUrl(url) {
      if (!url) return;
      try {
        const result = await window.SLLApi.call("open_external_url", url);
        if (!result?.ok) {
          this.toast(result?.error || this.t("error.generic"), true);
        }
      } catch (error) {
        this.toast(error?.message || String(error), true);
      }
    },

    modpackUpdateText(key) {
      const value = this.t(key);
      if (value && value !== key) return value;

      const lang = window.SLLState?.preferences?.language || "en";
      const fallback = {
        en: {
          "modpackUpdate.check": "Check modpack",
          "modpackUpdate.update": "Update modpack",
          "modpackUpdate.current": "Current",
          "modpackUpdate.latest": "Latest",
          "modpackUpdate.smartPrune": "Safe cleanup",
          "modpackUpdate.updateAvailable": "Modpack update available",
          "modpackUpdate.upToDate": "Modpack is up to date",
          "modpackUpdate.sourceModrinth": "Modrinth modpack",
          "modpackUpdate.sourceCurseForge": "CurseForge modpack",

          "modrinthModpack.hint": "This instance was installed from a Modrinth modpack. You can check for updates.",
          "modrinthModpack.updateHint": "The update will reinstall the latest compatible Modrinth modpack version into this instance.",
          "modrinthModpack.upToDateHint": "The installed version matches the latest compatible Modrinth version.",
          "modrinthModpack.smartPruneReady": "tracked files: {count}",
          "modrinthModpack.smartPruneLearning": "will start after the next managed install",
          "modrinthModpack.checked": "Modrinth modpack update check completed.",
          "modrinthModpack.confirmUpdate": "Update this Modrinth modpack in the selected instance?",
          "modrinthModpack.updated": "Modrinth modpack updated.",

          "curseforgeModpack.hint": "This instance was installed from a CurseForge modpack. You can check for updates and reopen the install report.",
          "curseforgeModpack.updateHint": "The update will reinstall the latest compatible CurseForge modpack manifest into this instance.",
          "curseforgeModpack.upToDateHint": "No newer compatible CurseForge file was found for the current Minecraft version and loader.",
          "curseforgeModpack.smartPruneReady": "tracked files: {count}",
          "curseforgeModpack.smartPruneLearning": "will start after the next managed install",
          "curseforgeModpack.checked": "CurseForge modpack update check completed.",
          "curseforgeModpack.confirmUpdate": "Update this CurseForge modpack in the selected instance?",
          "curseforgeModpack.updated": "CurseForge modpack updated.",
          "curseforgeModpack.prunedToast": "Removed obsolete files: {count}."
        },
        uk: {
          "modpackUpdate.check": "Перевірити модпак",
          "modpackUpdate.update": "Оновити модпак",
          "modpackUpdate.current": "Поточна",
          "modpackUpdate.latest": "Нова",
          "modpackUpdate.smartPrune": "Безпечне очищення",
          "modpackUpdate.updateAvailable": "Доступне оновлення модпака",
          "modpackUpdate.upToDate": "Модпак актуальний",
          "modpackUpdate.sourceModrinth": "Modrinth-модпак",
          "modpackUpdate.sourceCurseForge": "CurseForge-модпак",

          "modrinthModpack.hint": "Ця збірка встановлена з Modrinth-модпака. Можна перевірити оновлення.",
          "modrinthModpack.updateHint": "Оновлення перевстановить найновішу сумісну версію Modrinth-модпака в цій збірці.",
          "modrinthModpack.upToDateHint": "Встановлена версія збігається з найновішою сумісною версією Modrinth.",
          "modrinthModpack.smartPruneReady": "відстежуваних файлів: {count}",
          "modrinthModpack.smartPruneLearning": "почне працювати після наступного керованого встановлення",
          "modrinthModpack.checked": "Перевірку оновлень Modrinth-модпака завершено.",
          "modrinthModpack.confirmUpdate": "Оновити цей Modrinth-модпак у вибраній збірці?",
          "modrinthModpack.updated": "Modrinth-модпак оновлено.",

          "curseforgeModpack.hint": "Ця збірка встановлена з CurseForge-модпака. Можна перевірити оновлення та знову відкрити підсумок завантаження.",
          "curseforgeModpack.updateHint": "Оновлення перевстановить найновіший сумісний manifest CurseForge-модпака в цій збірці.",
          "curseforgeModpack.upToDateHint": "Новіший сумісний файл CurseForge для поточної версії Minecraft і завантажувача не знайдено.",
          "curseforgeModpack.smartPruneReady": "відстежуваних файлів: {count}",
          "curseforgeModpack.smartPruneLearning": "почне працювати після наступного керованого встановлення",
          "curseforgeModpack.checked": "Перевірку оновлень CurseForge-модпака завершено.",
          "curseforgeModpack.confirmUpdate": "Оновити цей CurseForge-модпак у вибраній збірці?",
          "curseforgeModpack.updated": "CurseForge-модпак оновлено.",
          "curseforgeModpack.prunedToast": "Видалено застарілих файлів: {count}."
        },
        kk: {
          "modpackUpdate.check": "Модпакты тексеру",
          "modpackUpdate.update": "Модпакты жаңарту",
          "modpackUpdate.current": "Ағымдағы",
          "modpackUpdate.latest": "Жаңа",
          "modpackUpdate.smartPrune": "Қауіпсіз тазалау",
          "modpackUpdate.updateAvailable": "Модпак жаңартуы қолжетімді",
          "modpackUpdate.upToDate": "Модпак өзекті",
          "modpackUpdate.sourceModrinth": "Modrinth модпагы",
          "modpackUpdate.sourceCurseForge": "CurseForge модпагы",

          "modrinthModpack.hint": "Бұл жинақ Modrinth модпагынан орнатылған. Жаңартуды тексеруге болады.",
          "modrinthModpack.updateHint": "Жаңарту осы жинаққа ең жаңа үйлесімді Modrinth модпак нұсқасын қайта орнатады.",
          "modrinthModpack.upToDateHint": "Орнатылған нұсқа ең жаңа үйлесімді Modrinth нұсқасымен сәйкес келеді.",
          "modrinthModpack.smartPruneReady": "бақыланатын файлдар: {count}",
          "modrinthModpack.smartPruneLearning": "келесі басқарылатын орнатудан кейін жұмыс істей бастайды",
          "modrinthModpack.checked": "Modrinth модпагының жаңартуын тексеру аяқталды.",
          "modrinthModpack.confirmUpdate": "Бұл Modrinth модпагын таңдалған жинақта жаңарту керек пе?",
          "modrinthModpack.updated": "Modrinth модпагы жаңартылды.",

          "curseforgeModpack.hint": "Бұл жинақ CurseForge модпагынан орнатылған. Жаңартуды тексеруге және орнату есебін қайта ашуға болады.",
          "curseforgeModpack.updateHint": "Жаңарту осы жинаққа ең жаңа үйлесімді CurseForge модпак manifest файлын қайта орнатады.",
          "curseforgeModpack.upToDateHint": "Ағымдағы Minecraft нұсқасы мен жүктеуші үшін жаңарақ CurseForge файлы табылмады.",
          "curseforgeModpack.smartPruneReady": "бақыланатын файлдар: {count}",
          "curseforgeModpack.smartPruneLearning": "келесі басқарылатын орнатудан кейін жұмыс істей бастайды",
          "curseforgeModpack.checked": "CurseForge модпагының жаңартуын тексеру аяқталды.",
          "curseforgeModpack.confirmUpdate": "Бұл CurseForge модпагын таңдалған жинақта жаңарту керек пе?",
          "curseforgeModpack.updated": "CurseForge модпагы жаңартылды.",
          "curseforgeModpack.prunedToast": "Ескірген файлдар жойылды: {count}."
        }
      };

      return fallback[lang]?.[key] || fallback.uk?.[key] || fallback.en?.[key] || key;
    },

    curseforgeCatalogHint(type) {
      if (type !== "modpack") return this.t("curseforge.readyHint");
      const key = "curseforge.modpackHint";
      const value = this.t(key);
      if (value && value !== key && !value.includes("окремим етапом") && !value.includes("separate stage")) return value;

      const lang = window.SLLState?.preferences?.language || "en";
      return {
        en: "Search and install CurseForge modpacks into the selected instance.",
        uk: "Шукайте та встановлюйте CurseForge-модпаки у вибрану збірку.",
        kk: "CurseForge модпактарын іздеп, таңдалған жинаққа орнатыңыз."
      }[lang] || "Search and install CurseForge modpacks into the selected instance.";
    },

    curseforgeModpackReportLabel() {
      const key = "curseforgeModpack.report";
      const value = this.t(key);
      if (value && value !== key) return value;
      const lang = window.SLLState?.preferences?.language || "en";
      return {
        en: "Install report",
        uk: "Підсумок завантаження",
        kk: "Жүктеу қорытындысы"
      }[lang] || "Install report";
    },

    modpackPreflightText(key) {
      const value = this.t(key);
      if (value && value !== key) return value;
      const lang = window.SLLState?.preferences?.language || "en";
      const fallback = {
        en: {
          "curseforgeModpackPreview.title": "CurseForge modpack preflight",
          "curseforgeModpackPreview.subtitle": "Installation is not started yet. This check only reads the modpack manifest.",
          "curseforgeModpackPreview.selectedInstance": "Selected instance",
          "curseforgeModpackPreview.packSettings": "Pack settings",
          "curseforgeModpackPreview.files": "Files",
          "curseforgeModpackPreview.available": "Available",
          "curseforgeModpackPreview.manual": "Manual required",
          "curseforgeModpackPreview.overrides": "Overrides",
          "curseforgeModpackPreview.reconfigure": "The selected instance will be reconfigured to this modpack's Minecraft version and loader, like Modrinth modpacks.",
          "curseforgeModpackPreview.noReconfigure": "The selected instance already matches the modpack version and loader.",
          "curseforgeModpackPreview.manualTitle": "Files requiring manual installation",
          "curseforgeModpackPreview.openProject": "Open project",
          "curseforgeModpackPreview.close": "Close",
          "curseforgeModpackPreview.copyList": "Copy list",
          "curseforge.installModpackHint": "Read the CurseForge modpack manifest and install it into the selected instance.",
          "curseforgeModpackPreview.install": "Install",
          "curseforgeModpackPreview.installConfirmFallback": "Install this CurseForge modpack into the selected instance?",
          "curseforgeModpackPreview.installDoneTitle": "CurseForge modpack installed",
          "curseforgeModpackPreview.installPartialTitle": "CurseForge modpack installed partially",
          "curseforgeModpackPreview.installDoneSummary": "The modpack was installed successfully.",
          "curseforgeModpackPreview.installPartialSummary": "The modpack was installed, but some files require manual installation.",
          "curseforgeModpackPreview.installed": "Installed",
          "curseforgeModpackPreview.alreadyInstalled": "Already installed",
          "curseforgeModpackPreview.openInstanceFolder": "Open instance folder",
          "curseforgeModpackPreview.folder": "Folder",
          "curseforgeModpackPreview.resultSubtitle": "Installation summary.",
          "curseforgeModpackPreview.resultToast": "CurseForge modpack installation finished.",
        },
        uk: {
          "curseforgeModpackPreview.title": "Перевірка CurseForge-модпака",
          "curseforgeModpackPreview.subtitle": "Встановлення ще не починається. Цей етап лише читає manifest модпака.",
          "curseforgeModpackPreview.selectedInstance": "Вибрана збірка",
          "curseforgeModpackPreview.packSettings": "Параметри модпака",
          "curseforgeModpackPreview.files": "Файли",
          "curseforgeModpackPreview.available": "Доступно",
          "curseforgeModpackPreview.manual": "Потрібно вручну",
          "curseforgeModpackPreview.overrides": "Overrides",
          "curseforgeModpackPreview.reconfigure": "Вибрана збірка буде переналаштована під версію Minecraft і завантажувач цього модпака, як у Modrinth-модпаках.",
          "curseforgeModpackPreview.noReconfigure": "Вибрана збірка вже відповідає версії та завантажувачу модпака.",
          "curseforgeModpackPreview.manualTitle": "Файли, які потрібно встановити вручну",
          "curseforgeModpackPreview.openProject": "Відкрити проєкт",
          "curseforgeModpackPreview.close": "Закрити",
          "curseforgeModpackPreview.copyList": "Скопіювати список",
          "curseforge.installModpackHint": "Прочитати manifest CurseForge-модпака та встановити його у вибрану збірку.",
          "curseforgeModpackPreview.install": "Встановити",
          "curseforgeModpackPreview.installConfirmFallback": "Встановити цей CurseForge-модпак у вибрану збірку?",
          "curseforgeModpackPreview.installDoneTitle": "CurseForge-модпак встановлено",
          "curseforgeModpackPreview.installPartialTitle": "CurseForge-модпак встановлено частково",
          "curseforgeModpackPreview.installDoneSummary": "Модпак успішно встановлено.",
          "curseforgeModpackPreview.installPartialSummary": "Модпак встановлено, але частину файлів потрібно додати вручну.",
          "curseforgeModpackPreview.installed": "Встановлено",
          "curseforgeModpackPreview.alreadyInstalled": "Уже було",
          "curseforgeModpackPreview.openInstanceFolder": "Відкрити папку збірки",
          "curseforgeModpackPreview.folder": "Папка",
          "curseforgeModpackPreview.resultSubtitle": "Підсумок встановлення.",
          "curseforgeModpackPreview.resultToast": "Встановлення CurseForge-модпака завершено.",
        },
        kk: {
          "curseforgeModpackPreview.title": "CurseForge модпагын алдын ала тексеру",
          "curseforgeModpackPreview.subtitle": "Орнату әлі басталмайды. Бұл кезең тек модпак manifest файлын оқиды.",
          "curseforgeModpackPreview.selectedInstance": "Таңдалған жинақ",
          "curseforgeModpackPreview.packSettings": "Модпак параметрлері",
          "curseforgeModpackPreview.files": "Файлдар",
          "curseforgeModpackPreview.available": "Қолжетімді",
          "curseforgeModpackPreview.manual": "Қолмен керек",
          "curseforgeModpackPreview.overrides": "Overrides",
          "curseforgeModpackPreview.reconfigure": "Таңдалған жинақ Modrinth модпактарындағыдай осы модпактың Minecraft нұсқасы мен жүктеушісіне қайта бапталады.",
          "curseforgeModpackPreview.noReconfigure": "Таңдалған жинақ модпак нұсқасы мен жүктеушісіне сәйкес келеді.",
          "curseforgeModpackPreview.manualTitle": "Қолмен орнатуды қажет ететін файлдар",
          "curseforgeModpackPreview.openProject": "Жобаны ашу",
          "curseforgeModpackPreview.close": "Жабу",
          "curseforgeModpackPreview.copyList": "Тізімді көшіру",
          "curseforge.installModpackHint": "CurseForge модпак manifest файлын оқып, оны таңдалған жинаққа орнату.",
          "curseforgeModpackPreview.resultSubtitle": "Орнату қорытындысы.",
          "curseforgeModpackPreview.resultToast": "CurseForge модпагын орнату аяқталды.",
        }
      };
      return fallback[lang]?.[key] || fallback.uk?.[key] || fallback.en?.[key] || key;
    },

    ensureCurseForgeModpackPreflightDom() {
      if ($("#curseforgeModpackPreflightBackdrop")) return;
      const wrapper = document.createElement("div");
      wrapper.innerHTML = `
        <div id="curseforgeModpackPreflightBackdrop" class="modal-backdrop hidden" aria-hidden="true">
          <section class="modal-card dependency-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="curseforgeModpackPreflightTitle">
            <header class="modal-card__header">
              <div>
                <div class="eyebrow">CurseForge</div>
                <h2 id="curseforgeModpackPreflightTitle"></h2>
                <p id="curseforgeModpackPreflightSubtitle" class="modal-subtitle"></p>
              </div>
              <button id="curseforgeModpackPreflightClose" class="icon-button" type="button" aria-label="Close">×</button>
            </header>
            <div class="dependency-preview">
              <div id="curseforgeModpackPreflightSummary" class="form-note"></div>
              <div id="curseforgeModpackPreflightCards" class="modpack-preflight__cards"></div>
              <div id="curseforgeModpackPreflightManual" class="dependency-preview__list"></div>
            </div>
            <footer class="dependency-preview__actions">
              <button id="curseforgeModpackPreflightCopy" class="button" type="button"></button>
              <button id="curseforgeModpackPreflightDone" class="button button--primary" type="button"></button>
            </footer>
          </section>
        </div>
      `.trim();
      document.body.appendChild(wrapper.firstElementChild);
    },

    formatCurseForgeManualList(plan, manualItems) {
      const pack = plan?.pack || {};
      const instance = plan?.target_instance || {};
      const commonNoDownload = "No downloadUrl returned by CurseForge API";

      const header = [
        this.modpackPreflightText("curseforgeModpackPreview.manualTitle"),
        "",
        pack.name || plan?.project?.title || "CurseForge modpack",
        `${pack.minecraft_version || instance.minecraft_version || "?"} · ${pack.loader || instance.loader || "vanilla"} ${pack.loader_version || ""}`.trim(),
        ""
      ];

      const lines = (manualItems || []).map((item, index) => {
        const reason = String(item.reason || "").trim();
        const block = [
          `${index + 1}. ${item.title || `Project ${item.project_id || "?"}`}`,
          `   Project ID: ${item.project_id || "?"}`,
          `   File ID: ${item.file_id || "?"}`,
          `   URL: ${item.project_url || ""}`
        ];

        if (reason && reason !== commonNoDownload) {
          block.push(`   Reason: ${reason}`);
        }

        return block.join("\n");
      });

      return [...header, ...lines].join("\n\n").trim();
    },

    showCurseForgeModpackPreflight(plan, options = {}) {
      this.ensureCurseForgeModpackPreflightDom();

      return new Promise(resolve => {
        const backdrop = $("#curseforgeModpackPreflightBackdrop");
        const title = $("#curseforgeModpackPreflightTitle");
        const subtitle = $("#curseforgeModpackPreflightSubtitle");
        const summary = $("#curseforgeModpackPreflightSummary");
        const cards = $("#curseforgeModpackPreflightCards");
        const manual = $("#curseforgeModpackPreflightManual");
        const close = $("#curseforgeModpackPreflightClose");
        const done = $("#curseforgeModpackPreflightDone");
        const copy = $("#curseforgeModpackPreflightCopy");

        if (!backdrop || !title || !cards || !manual || !done || !close || !copy) {
          resolve(window.confirm(this.modpackPreflightText("curseforgeModpackPreview.installConfirmFallback")));
          return;
        }

        const pack = plan.pack || {};
        const counts = plan.counts || {};
        const instance = plan.target_instance || {};
        const manualItems = plan.manual_items || [];
        const installMode = Boolean(options.install);

        title.textContent = this.modpackPreflightText("curseforgeModpackPreview.title");
        subtitle.textContent = this.modpackPreflightText("curseforgeModpackPreview.subtitle");
        done.textContent = installMode
          ? this.modpackPreflightText("curseforgeModpackPreview.install")
          : this.modpackPreflightText("curseforgeModpackPreview.close");
        copy.textContent = this.modpackPreflightText("curseforgeModpackPreview.copyList");
        copy.disabled = manualItems.length === 0;

        summary.textContent = pack.will_reconfigure_instance
          ? this.modpackPreflightText("curseforgeModpackPreview.reconfigure")
          : this.modpackPreflightText("curseforgeModpackPreview.noReconfigure");

        const stat = (label, value) => `
          <div class="modpack-preflight__stat">
            <div class="modpack-preflight__stat-value">${this.escape(String(value ?? "—"))}</div>
            <div class="modpack-preflight__stat-label">${this.escape(label)}</div>
          </div>
        `;

        cards.innerHTML = `
          <section class="modpack-preflight__panel">
            <h3>${this.escape(this.modpackPreflightText("curseforgeModpackPreview.selectedInstance"))}</h3>
            <p>${this.escape(instance.name || "—")}</p>
            <p>${this.escape(instance.minecraft_version || "—")} · ${this.escape(instance.loader || "vanilla")}</p>
          </section>
          <section class="modpack-preflight__panel">
            <h3>${this.escape(this.modpackPreflightText("curseforgeModpackPreview.packSettings"))}</h3>
            <p>${this.escape(pack.name || plan.project?.title || "CurseForge modpack")}</p>
            <p>${this.escape(pack.minecraft_version || "—")} · ${this.escape(pack.loader || "vanilla")} ${this.escape(pack.loader_version || "")}</p>
          </section>
          <section class="modpack-preflight__stats">
            ${stat(this.modpackPreflightText("curseforgeModpackPreview.files"), counts.manifest_files || 0)}
            ${stat(this.modpackPreflightText("curseforgeModpackPreview.available"), counts.available || 0)}
            ${stat(this.modpackPreflightText("curseforgeModpackPreview.manual"), counts.manual_required || 0)}
            ${stat(this.modpackPreflightText("curseforgeModpackPreview.overrides"), counts.overrides_files || 0)}
          </section>
        `;

        this.renderCurseForgeManualItems(manual, manualItems);
        manual.querySelectorAll("[data-cf-manual-open]").forEach(button => {
          button.addEventListener("click", () => this.openCurseForgeProjectUrl(button.dataset.cfManualOpen));
        });

        const manualText = this.formatCurseForgeManualList(plan, manualItems);

        const onCopy = async () => {
          if (!manualText) return;
          try {
            await navigator.clipboard.writeText(manualText);
            this.toast(this.t("common.copied") || "Copied");
          } catch (_error) {
            this.toast(manualText);
          }
        };

        const cleanup = result => {
          backdrop.classList.add("hidden");
          backdrop.setAttribute("aria-hidden", "true");
          close.removeEventListener("click", onCancel);
          done.removeEventListener("click", onDone);
          copy.removeEventListener("click", onCopy);
          backdrop.removeEventListener("click", onBackdrop);
          window.removeEventListener("keydown", onKey);
          resolve(result);
        };

        const onDone = () => cleanup(installMode);
        const onCancel = () => cleanup(false);
        const onBackdrop = event => {
          if (event.target === backdrop) cleanup(false);
        };
        const onKey = event => {
          if (event.key === "Escape") cleanup(false);
        };

        close.addEventListener("click", onCancel);
        done.addEventListener("click", onDone);
        copy.addEventListener("click", onCopy);
        backdrop.addEventListener("click", onBackdrop);
        window.addEventListener("keydown", onKey);

        backdrop.classList.remove("hidden");
        backdrop.setAttribute("aria-hidden", "false");
        setTimeout(() => done.focus(), 30);
      });
    },

    renderCurseForgeManualItems(container, manualItems) {
      if (!container) return;
      if (!manualItems?.length) {
        container.innerHTML = "";
        return;
      }

      container.innerHTML = `
        <div class="dependency-preview__section-title">${this.escape(this.modpackPreflightText("curseforgeModpackPreview.manualTitle"))}</div>
        ${manualItems.map(item => `
          <div class="dependency-preview__item">
            <div>
              <div class="dependency-preview__item-title">${this.escape(item.title || `Project ${item.project_id || "?"}`)}</div>
              <div class="dependency-preview__item-meta">
                Project ${this.escape(item.project_id || "?")} / File ${this.escape(item.file_id || "?")}<br>
                ${item.folder ? `${this.escape(this.modpackPreflightText("curseforgeModpackPreview.folder"))}: ${this.escape(item.folder)}<br>` : ""}
                ${item.filename ? `${this.escape(item.filename)}<br>` : ""}
                ${this.escape(String(item.reason || ""))}
              </div>
            </div>
            <button class="button button--compact" type="button" data-cf-manual-open="${this.escape(item.project_url || "")}">
              ${this.escape(this.modpackPreflightText("curseforgeModpackPreview.openProject"))}
            </button>
          </div>
        `).join("")}
      `;
    },

    showCurseForgeModpackInstallResult(result) {
      this.ensureCurseForgeModpackPreflightDom();

      const backdrop = $("#curseforgeModpackPreflightBackdrop");
      const title = $("#curseforgeModpackPreflightTitle");
      const subtitle = $("#curseforgeModpackPreflightSubtitle");
      const summary = $("#curseforgeModpackPreflightSummary");
      const cards = $("#curseforgeModpackPreflightCards");
      const manual = $("#curseforgeModpackPreflightManual");
      const close = $("#curseforgeModpackPreflightClose");
      const done = $("#curseforgeModpackPreflightDone");
      const copy = $("#curseforgeModpackPreflightCopy");

      if (!backdrop || !title || !cards || !manual || !done || !close || !copy) {
        this.toast(result?.message || this.t("curseforge.installed"));
        return;
      }

      const pack = result.pack || {};
      const counts = result.counts || {};
      const manualItems = result.manual_items || [];
      const partial = Boolean(result.partial || manualItems.length);

      title.textContent = partial
        ? this.modpackPreflightText("curseforgeModpackPreview.installPartialTitle")
        : this.modpackPreflightText("curseforgeModpackPreview.installDoneTitle");
      subtitle.textContent = this.modpackPreflightText("curseforgeModpackPreview.resultSubtitle");
      done.textContent = this.modpackPreflightText("curseforgeModpackPreview.close");
      copy.textContent = manualItems.length
        ? this.modpackPreflightText("curseforgeModpackPreview.copyList")
        : this.modpackPreflightText("curseforgeModpackPreview.openInstanceFolder");
      copy.disabled = false;

      summary.textContent = partial
        ? this.modpackPreflightText("curseforgeModpackPreview.installPartialSummary")
        : this.modpackPreflightText("curseforgeModpackPreview.installDoneSummary");

      const stat = (label, value) => `
        <div class="modpack-preflight__stat">
          <div class="modpack-preflight__stat-value">${this.escape(String(value ?? "—"))}</div>
          <div class="modpack-preflight__stat-label">${this.escape(label)}</div>
        </div>
      `;

      cards.innerHTML = `
        <section class="modpack-preflight__panel">
          <h3>${this.escape(pack.name || result.project?.title || "CurseForge modpack")}</h3>
          <p>${this.escape(pack.minecraft_version || "—")} · ${this.escape(pack.loader || "vanilla")} ${this.escape(pack.loader_version || "")}</p>
          <p>
            <button class="button button--compact" type="button" data-cf-open-instance-folder="${this.escape(result.target_instance_id || "")}">
              ${this.escape(this.modpackPreflightText("curseforgeModpackPreview.openInstanceFolder"))}
            </button>
          </p>
        </section>
        <section class="modpack-preflight__stats">
          ${stat(this.modpackPreflightText("curseforgeModpackPreview.installed"), counts.installed || 0)}
          ${stat(this.modpackPreflightText("curseforgeModpackPreview.alreadyInstalled"), counts.skipped_existing || 0)}
          ${stat(this.modpackPreflightText("curseforgeModpackPreview.manual"), counts.manual_required || 0)}
          ${stat(this.modpackPreflightText("curseforgeModpackPreview.overrides"), counts.overrides_files || 0)}
        </section>
      `;

      cards.querySelectorAll("[data-cf-open-instance-folder]").forEach(button => {
        button.addEventListener("click", async () => {
          const targetId = button.dataset.cfOpenInstanceFolder || result.target_instance_id || "";
          const opened = await window.SLLApi.call("open_instance_folder", targetId);
          if (!opened?.ok) this.toast(opened?.error || this.t("error.generic"), true);
        });
      });

      this.renderCurseForgeManualItems(manual, manualItems);
      manual.querySelectorAll("[data-cf-manual-open]").forEach(button => {
        button.addEventListener("click", () => this.openCurseForgeProjectUrl(button.dataset.cfManualOpen));
      });

      const manualText = this.formatCurseForgeManualList(result, manualItems);

      const onCopy = async () => {
        if (manualItems.length) {
          try {
            await navigator.clipboard.writeText(manualText);
            this.toast(this.t("common.copied") || "Copied");
          } catch (_error) {
            this.toast(manualText);
          }
          return;
        }
        const opened = await window.SLLApi.call("open_instance_folder", result.target_instance_id || "");
        if (!opened?.ok) this.toast(opened?.error || this.t("error.generic"), true);
      };

      const cleanup = () => {
        backdrop.classList.add("hidden");
        backdrop.setAttribute("aria-hidden", "true");
        close.removeEventListener("click", cleanup);
        done.removeEventListener("click", cleanup);
        copy.removeEventListener("click", onCopy);
        backdrop.removeEventListener("click", onBackdrop);
        window.removeEventListener("keydown", onKey);
      };

      const onBackdrop = event => {
        if (event.target === backdrop) cleanup();
      };
      const onKey = event => {
        if (event.key === "Escape") cleanup();
      };

      close.addEventListener("click", cleanup);
      done.addEventListener("click", cleanup);
      copy.addEventListener("click", onCopy);
      backdrop.addEventListener("click", onBackdrop);
      window.addEventListener("keydown", onKey);

      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
      setTimeout(() => done.focus(), 30);
    },

    async installCurseForgeProject(projectId) {
      const selected = this.selectedInstanceForCatalog();
      const project = (this.curseforgeResults || []).find(item => String(item.project_id || item.slug || "") === String(projectId));
      if (!project) {
        this.toast(this.t("curseforge.projectMissing"), true);
        return;
      }
      if (project.compatible_file?.download_available === false) {
        this.toast(this.t("curseforge.downloadUnavailableHint"), true);
        return;
      }

      const buttons = $$(`[data-curseforge-install="${CSS.escape(String(projectId))}"]`);
      buttons.forEach(button => {
        button.disabled = true;
        button.textContent = this.t("curseforge.installing");
      });

      try {
        if (!selected) {
          this.toast(this.t("curseforge.noInstanceError"), true);
          return;
        }

        const curseforgeFilters = this.collectCurseForgeFilters();
        const payload = {
          instance_id: selected?.id || "",
          project_id: projectId,
          file_id: project.compatible_file?.file_id || "",
          project_type: project.project_type,
          filters: {
            game_version: (curseforgeFilters.game_version || selected?.minecraft_version || ""),
            loader: ["mod", "modpack"].includes(project.project_type)
              ? (curseforgeFilters.loader || selected?.loader || "")
              : "",
            category_ids: curseforgeFilters.category_ids || []
          }
        };

        if (project.project_type === "modpack") {
          const plan = await window.SLLApi.call("preview_curseforge_modpack_install", payload);
          if (!plan?.ok) {
            this.toast(this.localizeMessage(plan?.error || this.t("error.generic")), true);
            return;
          }

          const confirmed = await this.showCurseForgeModpackPreflight(plan, { install: true });
          if (!confirmed) return;

          const result = await window.SLLApi.call("install_curseforge_modpack_project", payload);
          if (!result?.ok) {
            this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
            return;
          }

          if (result.state) this.setState(result.state);
          if (this.instanceWindowId === (result.target_instance_id || selected?.id || "")) {
            const refreshed = await window.SLLApi.call("get_instance_window_data", this.instanceWindowId);
            if (refreshed?.ok) this.renderInstanceWindow(refreshed);
          }
          this.showCurseForgeModpackInstallResult(result);
          this.toast(this.modpackPreflightText("curseforgeModpackPreview.resultToast"));
          return;
        }

        const confirmed = await this.confirmDependencyPlan("preview_curseforge_install", payload);
        if (!confirmed) return;

        const result = await window.SLLApi.call("install_curseforge_project", payload);

        if (!result?.ok) {
          this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
          return;
        }

        if (result.state) this.setState(result.state);
        const label = result.already_installed ? this.t("curseforge.alreadyInstalled") : this.t("curseforge.installed");
        const dependencyCount = Array.isArray(result.dependencies_installed) ? result.dependencies_installed.length : 0;
        const dependencySuffix = dependencyCount > 0
          ? ` (+${dependencyCount} ${this.t("curseforge.dependencies")})`
          : "";
        const message = `${label}: ${result.filename || project.title}${dependencySuffix}`;
        this.toast(message);
        this.appendLog(`${label} ${project.title} → ${result.folder || ""}/${result.filename || ""}${dependencySuffix}`);

        if (selected && this.instanceWindowId === selected.id) {
          const refreshed = await window.SLLApi.call("get_instance_window_data", selected.id);
          if (refreshed?.ok) this.renderInstanceWindow(refreshed);
        }
      } catch (error) {
        this.toast(error?.message || String(error), true);
      } finally {
        buttons.forEach(button => {
          button.disabled = false;
          button.textContent = this.t("curseforge.install");
        });
      }
    },

    formatNumber(value) {
      const number = Number(value || 0);
      if (number >= 1000000) return `${(number / 1000000).toFixed(1)}M`;
      if (number >= 1000) return `${(number / 1000).toFixed(1)}K`;
      return String(number);
    },

    async runAction(action) {
      if (action === "check_updates") {
        await this.checkUpdatesAndShow(false);
        return;
      }

      const result = action === "official_install"
        ? await window.SLLApi.call("install_official")
        : await window.SLLApi.call("run_action", action);

      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      if (result.preview) {
        this.toast(this.t("toast.planned"));
      }
    },

    async runCommand(command) {
      this.closeMenus();

      switch (command) {
        case "add-instance":
          await this.openInstanceEditor();
          break;
        case "edit-instance":
          await this.openInstanceEditor(window.SLLState.selected_instance_id || "");
          break;
        case "instance-window":
          await this.openInstanceWindow(window.SLLState.selected_instance_id || "");
          break;
        case "delete-selected-instance":
          await this.deleteSelectedInstance(window.SLLState.selected_instance_id || "");
          break;
        case "account-manager":
          await this.openAccountManager();
          break;
        case "launch-settings":
          await this.openLaunchSettings();
          break;
        case "install-official":
          await this.runAction("official_install");
          break;
        case "classic-ui":
          await this.openClassic(false);
          break;
        case "open-folder": {
          const result = await window.SLLApi.call("open_instance_folder", "");
          if (!result?.ok) this.toast(result?.error || this.t("error.generic"), true);
          break;
        }
        case "open-log":
          await window.SLLApi.call("open_log");
          break;
        case "github":
          await this.openConfiguredUrl("github_url");
          break;
        case "bug-report":
          await this.openConfiguredUrl("bug_report_url");
          break;
        case "community-site":
          await this.openConfiguredUrl("community_site_url");
          break;
        case "community-discord":
          await this.openConfiguredUrl("community_discord_url");
          break;
        case "check-updates":
          await this.runAction("check_updates");
          break;
        case "refresh-accounts":
          await this.refreshAppState(true);
          break;
        case "toggle-log":
          this.toggleLog();
          break;
        case "about":
          this.openAboutDialog();
          break;
      }
    },

    async openConfiguredUrl(key) {
      const url = window.SLLState?.launcher?.[key] || "";
      if (!url) {
        this.toast(this.t("error.generic"), true);
        return;
      }

      const result = await window.SLLApi.call("open_external_url", url);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
      }
    },

    openAboutDialog() {
      const launcher = window.SLLState?.launcher || {};
      const name = launcher.name || "StoneLight Launcher";
      const version = launcher.version || "0.6.71";
      const versionLabel = $("#aboutVersion");
      if (versionLabel) {
        versionLabel.textContent = `${name} v${version}`;
      }

      const backdrop = $("#aboutBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
    },

    closeAboutDialog() {
      const backdrop = $("#aboutBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
    },

    async refreshAppState(showToast = false) {
      try {
        const state = await window.SLLApi.call("get_app_state");
        this.setState(state);
        if (showToast) this.toast(this.t("account.refreshedList"));
      } catch (error) {
        this.toast(error?.message || String(error), true);
      }
    },

    async openInstanceWindow(instanceId = "") {
      this.closeMenus();
      this.hideContextMenu();

      const result = await window.SLLApi.call("get_instance_window_data", instanceId);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      this.instanceWindowId = result.instance?.id || "";
      this.renderInstanceWindow(result);

      const backdrop = $("#instanceWindowBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
    },

    closeInstanceWindow() {
      const backdrop = $("#instanceWindowBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
    },

    switchInstanceWindowTab(tabName) {
      $$("[data-instance-window-tab]").forEach(tab => {
        tab.classList.toggle("is-active", tab.dataset.instanceWindowTab === tabName);
      });
      $$("[data-instance-window-panel]").forEach(panel => {
        panel.classList.toggle("is-active", panel.dataset.instanceWindowPanel === tabName);
      });
    },

    renderInstanceWindow(data) {
      this.instanceWindowData = data;
      const instance = data.instance || {};
      const loader = instance.loader === "vanilla"
        ? "Vanilla"
        : `${this.capitalize(instance.loader)}${instance.loader_version ? ` ${instance.loader_version}` : ""}`;

      $("#instanceWindowTitle").textContent = instance.name || "—";
      $("#instanceWindowSubtitle").textContent = `Minecraft ${instance.minecraft_version || "?"} · ${loader}`;

      $("#instanceWindowSummary").innerHTML = [
        ["Minecraft", instance.minecraft_version || "?"],
        ["Loader", loader],
        [this.t("java.preset"), instance.java_preset || "auto"],
        [this.t("tile.installed"), this.t(instance.installed ? "tile.installed" : "tile.notInstalled")],
      ].map(([label, value]) => `
        <div class="summary-card">
          <div class="summary-card__label">${this.escape(label)}</div>
          <div class="summary-card__value">${this.escape(value)}</div>
        </div>
      `).join("");

      $("#forgeToolsRow").classList.toggle("hidden", (instance.loader || "").toLowerCase() !== "forge");
      this.renderOfficialUpdateNotice(data.official_update || null);
      this.renderModrinthModpackUpdateNotice(data.modrinth_modpack_update || null);
      this.renderCurseForgeModpackUpdateNotice(data.curseforge_modpack_update || null);
      const curseforgeReportButton = $("#curseforgeModpackReportButton");
      if (curseforgeReportButton) {
        curseforgeReportButton.classList.add("hidden");
        curseforgeReportButton.textContent = this.curseforgeModpackReportLabel();
      }

      this.renderFolderSubtabs(data.folders || []);
      this.populateWindowSettings(instance);
    },

    renderModrinthModpackUpdateNotice(update) {
      const box = $("#modrinthModpackUpdateNotice");
      const checkButton = $("#modrinthModpackCheckButton");
      const updateButton = $("#modrinthModpackUpdateButton");
      if (!box || !checkButton || !updateButton) return;

      // Stage 11.1: update controls live inside the notice card for both
      // Modrinth and CurseForge. Keep legacy action-row buttons hidden.
      checkButton.classList.add("hidden");
      updateButton.classList.add("hidden");

      if (!update?.supported) {
        box.classList.add("hidden");
        return;
      }

      const title = this.escape(update.title || "Modrinth modpack");
      const current = this.escape(update.current_version_number || update.current_version_id || "?");
      const latest = this.escape(update.latest_version_number || update.latest_version_id || "");
      const checked = Boolean(update.checked);
      const managedFiles = Number(update.managed_files || 0);
      const pruneText = update.smart_prune_available
        ? this.modpackUpdateText("modrinthModpack.smartPruneReady").replace("{count}", this.formatNumber(managedFiles))
        : this.modpackUpdateText("modrinthModpack.smartPruneLearning");

      const statusTitle = !checked
        ? `${this.modpackUpdateText("modpackUpdate.sourceModrinth")}: ${title}`
        : update.needs_update
          ? `${this.modpackUpdateText("modpackUpdate.updateAvailable")}: ${title}`
          : `${this.modpackUpdateText("modpackUpdate.upToDate")}: ${title}`;

      const statusText = !checked
        ? this.modpackUpdateText("modrinthModpack.hint")
        : update.needs_update
          ? this.modpackUpdateText("modrinthModpack.updateHint")
          : this.modpackUpdateText("modrinthModpack.upToDateHint");

      const latestRow = checked && update.needs_update
        ? `<div class="official-update-row"><span>${this.modpackUpdateText("modpackUpdate.latest")}</span><strong>${latest}</strong></div>`
        : "";

      const updateButtonHtml = checked && update.needs_update
        ? `<button class="button button--accent-soft button--compact" type="button" data-modpack-update-action="modrinth-update">${this.escape(this.modpackUpdateText("modpackUpdate.update"))}</button>`
        : "";

      box.classList.remove("hidden");
      box.innerHTML = `
        <div class="modpack-update-card__head">
          <div>
            <div class="official-update-notice__title">${checked && update.needs_update ? "⬆" : checked ? "✅" : "◇"} ${statusTitle}</div>
            <div class="official-update-notice__text">${statusText}</div>
          </div>
          <span class="modpack-update-card__source modpack-update-card__source--modrinth">Modrinth</span>
        </div>
        <div class="official-update-list">
          <div class="official-update-row"><span>${this.modpackUpdateText("modpackUpdate.current")}</span><strong>${current}</strong></div>
          ${latestRow}
          <div class="official-update-row"><span>${this.modpackUpdateText("modpackUpdate.smartPrune")}</span><strong>${this.escape(pruneText)}</strong></div>
        </div>
        <div class="modpack-update-card__actions">
          <button class="button button--compact" type="button" data-modpack-update-action="modrinth-check">${this.escape(this.modpackUpdateText("modpackUpdate.check"))}</button>
          ${updateButtonHtml}
        </div>
      `;

      box.querySelector('[data-modpack-update-action="modrinth-check"]')?.addEventListener("click", () => this.checkModrinthModpackUpdate());
      box.querySelector('[data-modpack-update-action="modrinth-update"]')?.addEventListener("click", () => this.applyModrinthModpackUpdate());
    },

    async checkModrinthModpackUpdate() {
      if (!this.instanceWindowId) return;
      const button = $("#modrinthModpackCheckButton");
      if (button) button.disabled = true;
      try {
        const result = await window.SLLApi.call("check_modrinth_modpack_update", this.instanceWindowId);
        if (!result?.ok && result?.error) {
          this.toast(this.localizeMessage(result.error), true);
          return;
        }
        this.instanceWindowData = this.instanceWindowData || {};
        this.instanceWindowData.modrinth_modpack_update = result;
        this.renderModrinthModpackUpdateNotice(result);
        this.toast(this.localizeMessage(result.message || this.modpackUpdateText("modrinthModpack.checked")));
      } catch (error) {
        this.toast(error?.message || String(error), true);
      } finally {
        if (button) button.disabled = false;
      }
    },

    async applyModrinthModpackUpdate() {
      if (!this.instanceWindowId) return;
      if (!window.confirm(this.modpackUpdateText("modrinthModpack.confirmUpdate"))) return;

      const button = $("#modrinthModpackUpdateButton");
      if (button) button.disabled = true;

      try {
        const result = await window.SLLApi.call("apply_modrinth_modpack_update", this.instanceWindowId);
        if (!result?.ok) {
          this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
          return;
        }

        const deletedCount = Number(result.smart_prune?.deleted_files || 0);
        const toastMessage = deletedCount > 0
          ? `${this.localizeMessage(result.message || this.modpackUpdateText("modrinthModpack.updated"))} ${this.modpackUpdateText("modrinthModpack.prunedToast").replace("{count}", this.formatNumber(deletedCount))}`
          : this.localizeMessage(result.message || this.modpackUpdateText("modrinthModpack.updated"));
        this.toast(toastMessage);
        if (result.state) {
          this.setState(result.state);
        }
        await this.refreshInstanceWindow();
      } catch (error) {
        this.toast(error?.message || String(error), true);
      } finally {
        if (button) button.disabled = false;
      }
    },

    renderCurseForgeModpackUpdateNotice(update) {
      const box = $("#curseforgeModpackUpdateNotice");
      const checkButton = $("#curseforgeModpackCheckButton");
      const updateButton = $("#curseforgeModpackUpdateButton");
      if (!box || !checkButton || !updateButton) return;

      // Stage 11.1: update controls live inside the notice card for both
      // Modrinth and CurseForge. Keep legacy action-row buttons hidden.
      checkButton.classList.add("hidden");
      updateButton.classList.add("hidden");

      if (!update?.supported) {
        box.classList.add("hidden");
        return;
      }

      const title = this.escape(update.title || "CurseForge modpack");
      const current = this.escape(update.current_display_name || update.current_file_name || update.current_file_id || "?");
      const latest = this.escape(update.latest_display_name || update.latest_file_name || update.latest_file_id || "");
      const checked = Boolean(update.checked);
      const managedFiles = Number(update.managed_files || 0);
      const pruneText = update.smart_prune_available
        ? this.modpackUpdateText("curseforgeModpack.smartPruneReady").replace("{count}", this.formatNumber(managedFiles))
        : this.modpackUpdateText("curseforgeModpack.smartPruneLearning");

      const statusTitle = !checked
        ? `${this.modpackUpdateText("modpackUpdate.sourceCurseForge")}: ${title}`
        : update.needs_update
          ? `${this.modpackUpdateText("modpackUpdate.updateAvailable")}: ${title}`
          : `${this.modpackUpdateText("modpackUpdate.upToDate")}: ${title}`;

      const statusText = !checked
        ? this.modpackUpdateText("curseforgeModpack.hint")
        : update.needs_update
          ? this.modpackUpdateText("curseforgeModpack.updateHint")
          : this.modpackUpdateText("curseforgeModpack.upToDateHint");

      const latestRow = checked && update.needs_update
        ? `<div class="official-update-row"><span>${this.modpackUpdateText("modpackUpdate.latest")}</span><strong>${latest}</strong></div>`
        : "";

      const updateButtonHtml = checked && update.needs_update
        ? `<button class="button button--accent-soft button--compact" type="button" data-modpack-update-action="curseforge-update">${this.escape(this.modpackUpdateText("modpackUpdate.update"))}</button>`
        : "";

      const reportButtonHtml = this.instanceWindowData?.curseforge_modpack_install_report?.supported
        ? `<button class="button button--compact" type="button" data-modpack-update-action="curseforge-report">${this.escape(this.curseforgeModpackReportLabel())}</button>`
        : "";

      box.classList.remove("hidden");
      box.innerHTML = `
        <div class="modpack-update-card__head">
          <div>
            <div class="official-update-notice__title">${checked && update.needs_update ? "⬆" : checked ? "✅" : "◇"} ${statusTitle}</div>
            <div class="official-update-notice__text">${statusText}</div>
          </div>
          <span class="modpack-update-card__source modpack-update-card__source--curseforge">CurseForge</span>
        </div>
        <div class="official-update-list">
          <div class="official-update-row"><span>${this.modpackUpdateText("modpackUpdate.current")}</span><strong>${current}</strong></div>
          ${latestRow}
          <div class="official-update-row"><span>${this.modpackUpdateText("modpackUpdate.smartPrune")}</span><strong>${this.escape(pruneText)}</strong></div>
        </div>
        <div class="modpack-update-card__actions">
          <button class="button button--compact" type="button" data-modpack-update-action="curseforge-check">${this.escape(this.modpackUpdateText("modpackUpdate.check"))}</button>
          ${updateButtonHtml}
          ${reportButtonHtml}
        </div>
      `;

      box.querySelector('[data-modpack-update-action="curseforge-check"]')?.addEventListener("click", () => this.checkCurseForgeModpackUpdate());
      box.querySelector('[data-modpack-update-action="curseforge-update"]')?.addEventListener("click", () => this.applyCurseForgeModpackUpdate());
      box.querySelector('[data-modpack-update-action="curseforge-report"]')?.addEventListener("click", () => {
        const report = this.instanceWindowData?.curseforge_modpack_install_report;
        if (report?.supported) this.showCurseForgeModpackInstallResult(report);
      });
    },

    async checkCurseForgeModpackUpdate() {
      if (!this.instanceWindowId) return;
      const button = $("#curseforgeModpackCheckButton");
      if (button) button.disabled = true;
      try {
        const result = await window.SLLApi.call("check_curseforge_modpack_update", this.instanceWindowId);
        if (!result?.ok && result?.error) {
          this.toast(this.localizeMessage(result.error), true);
          return;
        }
        this.instanceWindowData = this.instanceWindowData || {};
        this.instanceWindowData.curseforge_modpack_update = result;
        this.renderCurseForgeModpackUpdateNotice(result);
        this.toast(this.localizeMessage(result.message || this.modpackUpdateText("curseforgeModpack.checked")));
      } catch (error) {
        this.toast(error?.message || String(error), true);
      } finally {
        if (button) button.disabled = false;
      }
    },

    async applyCurseForgeModpackUpdate() {
      if (!this.instanceWindowId) return;
      if (!window.confirm(this.modpackUpdateText("curseforgeModpack.confirmUpdate"))) return;

      const button = $("#curseforgeModpackUpdateButton");
      if (button) button.disabled = true;

      try {
        const result = await window.SLLApi.call("apply_curseforge_modpack_update", this.instanceWindowId);
        if (!result?.ok) {
          this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
          return;
        }

        if (result.state) this.setState(result.state);
        await this.refreshInstanceWindow();
        this.showCurseForgeModpackInstallResult(result);

        const pruned = Number(result.counts?.pruned || result.smart_prune?.deleted_files || 0);
        const toastMessage = pruned > 0
          ? `${this.localizeMessage(result.message || this.modpackUpdateText("curseforgeModpack.updated"))} ${this.modpackUpdateText("curseforgeModpack.prunedToast").replace("{count}", this.formatNumber(pruned))}`
          : this.localizeMessage(result.message || this.modpackUpdateText("curseforgeModpack.updated"));
        this.toast(toastMessage);
      } catch (error) {
        this.toast(error?.message || String(error), true);
      } finally {
        if (button) button.disabled = false;
      }
    },

    renderOfficialUpdateNotice(update) {
      const box = $("#officialUpdateNotice");
      const button = $("#officialUpdateButton");

      if (!update?.official) {
        box.classList.add("hidden");
        button.classList.add("hidden");
        return;
      }

      button.classList.toggle("hidden", !update.needs_update);

      if (!update.needs_update) {
        box.classList.remove("hidden");
        box.innerHTML = `
          <div class="official-update-notice__title">✅ ${this.t("instanceWindow.officialUpToDate")}</div>
          <div class="official-update-notice__text">${this.t("instanceWindow.officialUpToDateHint")}</div>
        `;
        return;
      }

      const rows = (update.changes || []).slice(0, 6).map(change => `
        <div class="official-update-row">
          <span>${this.escape(change.label)}</span>
          <strong>${this.escape(change.current)} → ${this.escape(change.target)}</strong>
        </div>
      `).join("");

      const prefix = update.installed
        ? this.t("instanceWindow.officialUpdateAvailable")
        : this.t("instanceWindow.officialNotInstalled");

      box.classList.remove("hidden");
      box.innerHTML = `
        <div class="official-update-notice__title">⚙ ${prefix}</div>
        <div class="official-update-notice__text">${this.t("instanceWindow.officialUpdateHint")}</div>
        <div class="official-update-list">${rows || `<div class="official-update-row"><span>${this.t("instanceWindow.modsMayNeedUpdate")}</span><strong>${this.t("instanceWindow.updateRecommended")}</strong></div>`}</div>
      `;
    },

    renderFolderSubtabs(folders) {
      const preferred = ["mods", "resourcepacks", "shaderpacks", "config", "saves", "screenshots", "logs"];
      const available = folders.filter(folder => folder.key !== "root");
      const sorted = available.sort((a, b) => preferred.indexOf(a.key) - preferred.indexOf(b.key));
      if (!sorted.some(folder => folder.key === this.currentFolderKey)) {
        this.currentFolderKey = sorted[0]?.key || "mods";
      }

      $("#folderSubtabs").innerHTML = sorted.map(folder => `
        <button class="folder-subtab${folder.key === this.currentFolderKey ? " is-active" : ""}" type="button" data-folder-subtab="${this.escape(folder.key)}">
          ${this.escape(this.t(`folder.${folder.key}`) || folder.label)}
        </button>
      `).join("");

      $$("[data-folder-subtab]").forEach(button => {
        button.addEventListener("click", () => this.switchFolderSubtab(button.dataset.folderSubtab));
      });

      this.renderFolderFiles(
        this.currentFolderKey,
        this.instanceWindowData?.folder_files?.[this.currentFolderKey] || []
      );
    },

    async switchFolderSubtab(key) {
      this.currentFolderKey = key;
      $$(".folder-subtab").forEach(button => {
        button.classList.toggle("is-active", button.dataset.folderSubtab === key);
      });
      if (key === "logs") {
        this.renderFolderFiles("logs", []);
        return;
      }
      await this.refreshCurrentFolder();
    },

    renderFolderFiles(folderKey, files) {
      const folder = (this.instanceWindowData?.folders || []).find(item => item.key === folderKey);
      $("#folderPanelTitle").textContent = this.t(`folder.${folderKey}`) || folderKey;
      $("#folderPanelPath").textContent = folder?.path || "";

      $("#refreshFolderButton").textContent = this.t(folderKey === "logs" ? "console.clear" : "instanceWindow.refreshMods");
      $("#openCurrentFolderButton").textContent = this.t("instanceWindow.openFolder");

      const list = $("#folderFileList");
      list.dataset.folderKey = folderKey;

      if (folderKey === "logs") {
        list.classList.add("hidden");
        $("#folderFileEmpty").classList.add("hidden");
        $("#instanceConsoleOutput").classList.remove("hidden");
        this.renderInstanceConsole();
        return;
      }

      $("#instanceConsoleOutput").classList.add("hidden");
      list.classList.remove("hidden");
      $("#folderFileEmpty").classList.toggle("hidden", files.length > 0);

      if (folderKey === "screenshots") {
        this.renderScreenshotGrid(files.filter(file => file.is_image));
        return;
      }

      list.classList.remove("screenshot-grid");
      list.innerHTML = files.map(file => {
        if (file.is_dir) {
          return `
            <div class="mod-row">
              <span>📁</span>
              <div>
                <div class="mod-row__name">${this.escape(file.display_name || file.filename)}</div>
                <div class="mod-row__meta">Folder</div>
              </div>
              <span></span>
            </div>
          `;
        }

        const toggle = file.toggleable
          ? `<input class="mod-row__check" type="checkbox" ${file.enabled ? "checked" : ""} data-folder-toggle="${this.escape(file.filename)}">`
          : `<span></span>`;
        const status = file.toggleable
          ? this.t(file.enabled ? "instanceWindow.enabled" : "instanceWindow.disabled")
          : this.formatBytes(file.size_bytes || 0);
        return `
          <div class="mod-row${file.toggleable && !file.enabled ? " is-disabled" : ""}">
            ${toggle}
            <div>
              <div class="mod-row__name">${this.escape(file.display_name || file.filename)}</div>
              <div class="mod-row__meta">${status} · ${this.formatBytes(file.size_bytes || 0)}</div>
            </div>
            <div class="folder-row__actions">
              <button class="button button--danger-soft button--compact" type="button" data-folder-delete="${this.escape(file.filename)}">
                ${this.t("instanceWindow.deleteMod")}
              </button>
            </div>
          </div>
        `;
      }).join("");

      $$("[data-folder-toggle]").forEach(input => {
        input.addEventListener("change", () => this.toggleFolderFile(input.dataset.folderToggle, input.checked));
      });
      $$("[data-folder-delete]").forEach(button => {
        button.addEventListener("click", () => this.deleteFolderFile(button.dataset.folderDelete));
      });
    },

    renderScreenshotGrid(files) {
      files = [...files].sort((a, b) => (b.modified || 0) - (a.modified || 0));
      this.screenshotPreviewFiles = files.map(file => file.filename);
      $("#folderFileList").classList.add("screenshot-grid");
      $("#folderFileEmpty").classList.toggle("hidden", files.length > 0);
      $("#folderFileList").innerHTML = files.map(file => {
        const thumb = file.thumbnail_data_url
          ? `<img src="${file.thumbnail_data_url}" alt="">`
          : `<span>🖼</span>`;
        return `
          <article class="screenshot-card">
            <button class="screenshot-card__thumb" type="button" data-screenshot-preview="${this.escape(file.filename)}">
              ${thumb}
            </button>
            <div class="screenshot-card__body">
              <div class="screenshot-card__name">${this.escape(file.filename)}</div>
              <div class="mod-row__meta">${this.formatBytes(file.size_bytes || 0)}</div>
              <div class="folder-row__actions folder-row__actions--icons">
                <button
                  class="icon-button screenshot-action-button"
                  type="button"
                  data-screenshot-preview="${this.escape(file.filename)}"
                  title="${this.t("screenshots.view")}"
                  aria-label="${this.t("screenshots.view")}"
                >👁</button>
                <button
                  class="icon-button screenshot-action-button screenshot-action-button--danger"
                  type="button"
                  data-folder-delete="${this.escape(file.filename)}"
                  title="${this.t("screenshots.delete")}"
                  aria-label="${this.t("screenshots.delete")}"
                >×</button>
              </div>
            </div>
          </article>
        `;
      }).join("");

      $$("[data-screenshot-preview]").forEach(button => {
        button.addEventListener("click", () => this.previewScreenshot(button.dataset.screenshotPreview));
      });
      $$("[data-folder-delete]").forEach(button => {
        button.addEventListener("click", () => this.deleteFolderFile(button.dataset.folderDelete));
      });
    },

    async refreshCurrentFolder() {
      if (!this.instanceWindowId) return;
      if (this.currentFolderKey === "logs") {
        this.clearInstanceConsole();
        return;
      }
      const result = await window.SLLApi.call("list_instance_folder", this.instanceWindowId, this.currentFolderKey);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }
      if (!this.instanceWindowData) this.instanceWindowData = {};
      if (!this.instanceWindowData.folder_files) this.instanceWindowData.folder_files = {};
      this.instanceWindowData.folder_files[this.currentFolderKey] = result.files || [];
      const folder = (this.instanceWindowData.folders || []).find(item => item.key === this.currentFolderKey);
      if (folder && result.path) folder.path = result.path;
      this.renderFolderFiles(this.currentFolderKey, result.files || []);
    },

    async toggleFolderFile(filename, enabled) {
      const result = await window.SLLApi.call("set_folder_file_enabled", this.instanceWindowId, this.currentFolderKey, filename, enabled);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        await this.refreshCurrentFolder();
        return;
      }
      this.renderFolderFiles(this.currentFolderKey, result.files || []);
      this.toast(this.t("instanceWindow.folderItemUpdated"));
    },

    async deleteFolderFile(filename) {
      if (!window.confirm(this.t("instanceWindow.deleteModConfirm"))) return;
      const result = await window.SLLApi.call("delete_folder_file", this.instanceWindowId, this.currentFolderKey, filename);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }
      this.renderFolderFiles(this.currentFolderKey, result.files || []);
      this.toast(this.t("instanceWindow.folderItemDeleted"));
    },

    async previewScreenshot(filename) {
      const index = this.screenshotPreviewFiles.indexOf(filename);
      this.screenshotPreviewIndex = index >= 0 ? index : -1;
      await this.loadScreenshotPreview(filename);
    },

    async loadScreenshotPreview(filename) {
      const result = await window.SLLApi.call("get_screenshot_data", this.instanceWindowId, filename);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      $("#screenshotPreviewTitle").textContent = result.filename || filename;
      $("#screenshotPreviewImage").src = result.data_url;

      const hasMany = this.screenshotPreviewFiles.length > 1;
      $("#screenshotPreviewPrev").disabled = !hasMany;
      $("#screenshotPreviewNext").disabled = !hasMany;

      $("#screenshotPreviewBackdrop").classList.remove("hidden");
      $("#screenshotPreviewBackdrop").setAttribute("aria-hidden", "false");
    },

    showAdjacentScreenshot(step) {
      if (!this.screenshotPreviewFiles.length) return;
      if (this.screenshotPreviewIndex < 0) this.screenshotPreviewIndex = 0;
      const count = this.screenshotPreviewFiles.length;
      this.screenshotPreviewIndex = (this.screenshotPreviewIndex + step + count) % count;
      const filename = this.screenshotPreviewFiles[this.screenshotPreviewIndex];
      if (filename) this.loadScreenshotPreview(filename);
    },

    closeScreenshotPreview() {
      $("#screenshotPreviewBackdrop").classList.add("hidden");
      $("#screenshotPreviewBackdrop").setAttribute("aria-hidden", "true");
      $("#screenshotPreviewImage").src = "";
      this.screenshotPreviewIndex = -1;
    },

    async openScreenshot(filename) {
      const result = await window.SLLApi.call("open_instance_subfolder", this.instanceWindowId, "screenshots");
      if (!result?.ok) this.toast(result?.error || this.t("error.generic"), true);
    },

    async copyScreenshotPath(filename) {
      const result = await window.SLLApi.call("copy_screenshot_path", this.instanceWindowId, filename);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }
      this.toast(this.t("screenshots.pathCopied"));
    },

    async loadWindowMinecraftVersionOptions() {
      const button = $("#windowSettingsLoadMinecraftVersionsButton");
      const note = $("#windowSettingsMinecraftVersionsNote");

      if (button.disabled) {
        note.textContent = this.t("editor.lockedVersionControls");
        return;
      }

      button.disabled = true;
      note.textContent = this.t("picker.loading");
      try {
        const includeSnapshots = $("#windowSettingsVersionType").value === "snapshot";
        const result = await window.SLLApi.call("get_minecraft_version_options", includeSnapshots);
        if (!result?.ok) {
          note.textContent = result?.error || this.t("editor.versionsFailed");
          return;
        }

        const versions = result.versions || [];
        note.textContent = `${this.t("picker.loaded")}: ${versions.length}`;
        this.openVersionPicker("window-minecraft", versions, this.t("picker.minecraft"), $("#windowSettingsMinecraft").value.trim());
      } catch (error) {
        note.textContent = error?.message || String(error);
      } finally {
        button.disabled = false;
      }
    },

    async loadWindowLoaderVersionOptions() {
      const loader = $("#windowSettingsLoader").value;
      const minecraftVersion = $("#windowSettingsMinecraft").value.trim();
      const input = $("#windowSettingsLoaderVersion");
      const button = $("#windowSettingsLoadLoaderVersionsButton");
      const note = $("#windowSettingsLoaderVersionsNote");

      if (button.disabled) {
        note.textContent = this.t("editor.lockedVersionControls");
        return;
      }

      if (loader === "vanilla") {
        input.value = "";
        note.textContent = this.t("editor.vanillaNoLoader");
        return;
      }

      if (!minecraftVersion) {
        note.textContent = this.t("editor.minecraftFirst");
        return;
      }

      button.disabled = true;
      note.textContent = this.t("picker.loading");
      try {
        const result = await window.SLLApi.call("get_loader_version_options", loader, minecraftVersion, true);
        if (!result?.ok) {
          note.textContent = result?.error || this.t("editor.versionsFailed");
          return;
        }

        const versions = result.versions || [];
        note.textContent = `${this.t("picker.loaded")}: ${versions.length}`;
        this.openVersionPicker("window-loader", versions, `${this.t("picker.loader")} · ${loader}`, input.value.trim());
      } catch (error) {
        note.textContent = error?.message || String(error);
      } finally {
        button.disabled = false;
      }
    },

    populateWindowSettings(instance) {
      $("#windowSettingsName").value = instance.name || "";
      $("#windowSettingsMinecraft").value = instance.minecraft_version || "";
      $("#windowSettingsVersionType").value = instance.version_type || "release";
      $("#windowSettingsLoader").value = instance.loader || "vanilla";
      $("#windowSettingsLoaderVersion").value = instance.loader_version || "";
      $("#windowSettingsJavaPreset").value = instance.java_preset || "auto";
      $("#windowSettingsJavaPath").value = instance.java_executable || "";
      $("#windowSettingsMinecraftVersionsNote").textContent = "";
      $("#windowSettingsLoaderVersionsNote").textContent = "";

      const locked = Boolean(instance.locked || instance.official);
      $("#windowSettingsLockedNote").classList.toggle("hidden", !locked);
      for (const element of [
        $("#windowSettingsName"),
        $("#windowSettingsMinecraft"),
        $("#windowSettingsVersionType"),
        $("#windowSettingsLoader"),
        $("#windowSettingsLoaderVersion")
      ]) {
        element.disabled = locked;
      }
      this.syncWindowSettingsFields();
    },

    syncWindowSettingsFields() {
      const manual = $("#windowSettingsJavaPreset").value === "manual";
      $("#windowSettingsJavaPathField").classList.toggle("hidden", !manual);
      $("#windowSettingsJavaPath").disabled = !manual;
      if (!manual) $("#windowSettingsJavaPath").value = "";

      const loader = $("#windowSettingsLoader").value;
      const locked = $("#windowSettingsMinecraft").disabled;
      $("#windowSettingsLoaderVersion").disabled = locked || loader === "vanilla";
      $("#windowSettingsLoadMinecraftVersionsButton").disabled = locked;
      $("#windowSettingsLoadLoaderVersionsButton").disabled = locked || loader === "vanilla";

      if (locked) {
        $("#windowSettingsMinecraftVersionsNote").textContent = this.t("editor.lockedVersionControls");
        $("#windowSettingsLoaderVersionsNote").textContent = this.t("editor.lockedVersionControls");
      } else if (loader === "vanilla") {
        $("#windowSettingsLoaderVersion").value = "";
        $("#windowSettingsLoaderVersionsNote").textContent = this.t("editor.vanillaNoLoader");
      }
    },

    windowSettingsPayload() {
      return {
        name: $("#windowSettingsName").value.trim(),
        minecraft_version: $("#windowSettingsMinecraft").value.trim(),
        version_type: $("#windowSettingsVersionType").value,
        loader: $("#windowSettingsLoader").value,
        loader_version: $("#windowSettingsLoaderVersion").value.trim(),
        java_preset: $("#windowSettingsJavaPreset").value,
        java_executable: $("#windowSettingsJavaPath").value.trim()
      };
    },

    async submitWindowSettings(event) {
      event.preventDefault();
      $("#windowSettingsError").classList.add("hidden");
      const button = $("#windowSettingsSave");
      button.disabled = true;
      try {
        const result = await window.SLLApi.call("update_instance", this.instanceWindowId, this.windowSettingsPayload());
        if (!result?.ok) {
          $("#windowSettingsError").textContent = result?.error || this.t("error.generic");
          $("#windowSettingsError").classList.remove("hidden");
          return;
        }
        if (result.state) this.setState(result.state);
        this.toast(this.t("editor.updated"));
        await this.refreshInstanceWindow();
      } catch (error) {
        $("#windowSettingsError").textContent = error?.message || String(error);
        $("#windowSettingsError").classList.remove("hidden");
      } finally {
        button.disabled = false;
      }
    },

    async refreshInstanceWindow() {
      if (!this.instanceWindowId) return;
      const result = await window.SLLApi.call("get_instance_window_data", this.instanceWindowId);
      if (result?.ok) {
        this.renderInstanceWindow(result);
      }
    },

    async openInstanceSubfolder(key) {
      const result = await window.SLLApi.call("open_instance_subfolder", this.instanceWindowId || "", key);
      if (!result?.ok) this.toast(result?.error || this.t("error.generic"), true);
    },

    async runInstanceWindowAction(action) {
      if (action === "play") {
        await this.runAction("play");
      } else if (action === "update") {
        await this.runAction("update");
        await this.refreshInstanceWindow();
      } else if (action === "modrinth-modpack-check") {
        await this.checkModrinthModpackUpdate();
      } else if (action === "modrinth-modpack-update") {
        await this.applyModrinthModpackUpdate();
      } else if (action === "curseforge-modpack-check") {
        await this.checkCurseForgeModpackUpdate();
      } else if (action === "curseforge-modpack-update") {
        await this.applyCurseForgeModpackUpdate();
      } else if (action === "stop") {
        await this.runAction("stop");
      } else if (action === "folder") {
        await this.openInstanceSubfolder("root");
      } else if (action === "curseforge-modpack-report") {
        const report = this.instanceWindowData?.curseforge_modpack_install_report;
        if (report?.supported) {
          this.showCurseForgeModpackInstallResult(report);
        } else {
          const result = await window.SLLApi.call("get_curseforge_modpack_install_report", this.instanceWindowId || window.SLLState.selected_instance_id || "");
          if (result?.ok && result.report?.supported) this.showCurseForgeModpackInstallResult(result.report);
          else this.toast(result?.error || this.t("error.generic"), true);
        }
      } else if (action === "settings") {
        this.switchInstanceWindowTab("settings");
      } else if (action === "delete") {
        await this.deleteSelectedInstance(this.instanceWindowId || window.SLLState.selected_instance_id || "");
      } else if (action === "forge-manual") {
        await this.runAction("forge_manual");
      } else if (action === "forge-repair") {
        await this.runAction("forge_repair");
      } else if (action === "forge-check") {
        await this.runAction("forge_check");
      }
    },

    async deleteSelectedInstance(instanceId = "") {
      const targetId = instanceId || window.SLLState.selected_instance_id || "";
      if (!targetId) return;

      const confirmed = await this.confirmDeleteInstance(targetId);
      if (!confirmed) return;

      const result = await window.SLLApi.call("delete_instance", targetId, true);
      if (!result?.ok) {
        this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
        return;
      }

      if (result.state) this.setState(result.state);
      if (this.instanceWindowId === targetId) this.closeInstanceWindow();
      this.toast(
        result.files_missing
          ? this.deleteInstanceText("instanceDelete.deletedMissing")
          : this.deleteInstanceText("instanceDelete.deleted")
      );
    },

    async openLaunchSettings() {
      this.closeMenus();
      this.hideContextMenu();

      const result = await window.SLLApi.call("get_launch_settings_data");
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      this.renderLaunchSettings(result.settings || {});
      const backdrop = $("#launchSettingsBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
    },

    closeLaunchSettings() {
      const backdrop = $("#launchSettingsBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
    },

    renderLaunchSettings(settings) {
      $("#globalRamMinInput").value = settings.ram_min_mb || "";
      $("#globalRamMaxInput").value = settings.ram_max_mb || "";
      $("#globalWindowModeSelect").value = settings.window_mode || "unchanged";
      $("#globalWindowWidthInput").value = settings.window_width || "";
      $("#globalWindowHeightInput").value = settings.window_height || "";
      this.applyingGraphicsProfile = true;
      $("#globalGraphicsProfileSelect").value = settings.graphics_profile || "custom";
      $("#globalRenderDistanceInput").value = settings.render_distance || "";
      $("#globalSimulationDistanceInput").value = settings.simulation_distance || "";
      $("#globalFpsLimitInput").value = settings.fps_limit || "";
      $("#globalVsyncSelect").value = settings.vsync || "unchanged";
      $("#globalGraphicsSelect").value = settings.graphics || "unchanged";
      $("#globalParticlesSelect").value = settings.particles || "unchanged";
      this.applyingGraphicsProfile = false;
      this.setLaunchSettingsError("");
    },

    applySelectedGraphicsProfile() {
      const profile = $("#globalGraphicsProfileSelect").value || "custom";
      if (profile === "custom") return;
      const values = this.graphicsProfiles[profile];
      if (!values) return;
      this.applyingGraphicsProfile = true;
      $("#globalRenderDistanceInput").value = values.render_distance;
      $("#globalSimulationDistanceInput").value = values.simulation_distance;
      $("#globalFpsLimitInput").value = values.fps_limit;
      $("#globalVsyncSelect").value = values.vsync;
      $("#globalGraphicsSelect").value = values.graphics;
      $("#globalParticlesSelect").value = values.particles;
      this.applyingGraphicsProfile = false;
    },

    markGraphicsProfileCustom() {
      if (this.applyingGraphicsProfile) return;
      const select = $("#globalGraphicsProfileSelect");
      if (!select || select.value === "custom") return;
      select.value = "custom";
    },

    launchSettingsPayload() {
      return {
        ram_min_mb: $("#globalRamMinInput").value.trim(),
        ram_max_mb: $("#globalRamMaxInput").value.trim(),
        window_mode: $("#globalWindowModeSelect").value,
        window_width: $("#globalWindowWidthInput").value.trim(),
        window_height: $("#globalWindowHeightInput").value.trim(),
        render_distance: $("#globalRenderDistanceInput").value.trim(),
        simulation_distance: $("#globalSimulationDistanceInput").value.trim(),
        fps_limit: $("#globalFpsLimitInput").value.trim(),
        vsync: $("#globalVsyncSelect").value,
        graphics: $("#globalGraphicsSelect").value,
        particles: $("#globalParticlesSelect").value,
        graphics_profile: $("#globalGraphicsProfileSelect").value
      };
    },

    async submitLaunchSettings(event) {
      event.preventDefault();
      this.setLaunchSettingsError("");
      const button = $("#launchSettingsSave");
      button.disabled = true;

      try {
        const result = await window.SLLApi.call("save_launch_settings", this.launchSettingsPayload());
        if (!result?.ok) {
          this.setLaunchSettingsError(result?.error || this.t("error.generic"));
          return;
        }

        if (result.state) this.setState(result.state);
        this.toast(this.t("launch.saved"));
        this.closeLaunchSettings();
      } catch (error) {
        this.setLaunchSettingsError(error?.message || String(error));
      } finally {
        button.disabled = false;
      }
    },

    resetLaunchSettingsForm() {
      this.renderLaunchSettings({
        ram_min_mb: "",
        ram_max_mb: "",
        window_mode: "unchanged",
        window_width: "",
        window_height: "",
        render_distance: "",
        simulation_distance: "",
        fps_limit: "",
        vsync: "unchanged",
        graphics: "unchanged",
        particles: "unchanged",
        graphics_profile: "unchanged"
      });
    },

    setLaunchSettingsError(message) {
      const box = $("#launchSettingsError");
      box.textContent = message ? this.localizeMessage(message) : "";
      box.classList.toggle("hidden", !message);
    },

    async openAccountManager() {
      this.closeMenus();
      this.hideContextMenu();
      this.setAccountManagerError("");

      const result = await window.SLLApi.call("get_account_manager_data");
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      this.accountManagerSelectedId =
        result.selected_account_id
        || (result.accounts?.[0]?.id || "");
      this.renderAccountManager(result);

      const backdrop = $("#accountManagerBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
      setTimeout(() => $("#offlineAccountNameInput").focus(), 30);
    },

    closeAccountManager() {
      const backdrop = $("#accountManagerBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
      this.setAccountManagerError("");
    },

    renderAccountManager(data = null) {
      const accounts = data?.accounts || window.SLLState.accounts || [];
      const selectedId = this.accountManagerSelectedId || data?.selected_account_id || window.SLLState.selected_account_id || "";
      const hasLicensed = data?.has_licensed_account ?? accounts.some(item => item.licensed);
      const canAddOffline = Boolean(data?.can_add_offline ?? hasLicensed);

      $("#accountManagerList").innerHTML = accounts.map(account => {
        const selected = account.id === selectedId;
        return `
          <button class="account-row${selected ? " is-selected" : ""}" type="button" data-account-row="${this.escape(account.id)}">
            <span class="account-row__avatar account-avatar">
              <img src="${this.escape(account.avatar_url || "https://crafthead.net/helm/Steve")}" alt="" loading="lazy" onerror="this.src='https://crafthead.net/helm/Steve'">
            </span>
            <span>
              <span class="account-row__name">${this.escape(account.username)}</span>
              <span class="account-row__type">${this.t(account.licensed ? "account.licensed" : "account.offline")}</span>
            </span>
            ${selected ? `<span class="account-row__badge">${this.t("account.selected")}</span>` : ""}
          </button>
        `;
      }).join("");

      $("#accountManagerEmpty").classList.toggle("hidden", accounts.length > 0);
      $("#deleteAccountButton").disabled = !selectedId;
      const selectedAccount = accounts.find(item => item.id === selectedId) || null;
      $("#refreshAccountButton").disabled = !selectedAccount || !selectedAccount.licensed;
      $("#addOfflineAccountButton").disabled = !canAddOffline;
      $("#offlineAccountNameInput").disabled = !canAddOffline;
      $("#offlineAccountNote").textContent = this.t(canAddOffline ? "account.offlineAllowed" : "account.offlineLocked");

      $$("[data-account-row]").forEach(button => {
        button.addEventListener("click", async () => {
          await this.selectAccountFromManager(button.dataset.accountRow);
        });
      });
    },

    async selectAccountFromManager(accountId) {
      if (!accountId) return;
      const result = await window.SLLApi.call("select_account", accountId);
      if (!result?.ok) {
        this.setAccountManagerError(result?.error || this.t("error.generic"));
        return;
      }
      if (result.state) this.setState(result.state);
      this.accountManagerSelectedId = accountId;
      const manager = await window.SLLApi.call("get_account_manager_data");
      if (manager?.ok) this.renderAccountManager(manager);
    },

    async addMicrosoftAccount() {
      this.setAccountManagerError("");
      const button = $("#addMicrosoftAccountButton");
      const previousText = button.textContent;
      button.disabled = true;
      button.textContent = this.t("account.microsoftOpening");

      try {
        const start = await window.SLLApi.call("start_microsoft_login");
        if (!start?.ok) {
          this.setAccountManagerError(start?.error || this.t("error.generic"));
          return;
        }

        this.toast(start.message || this.t("account.microsoftOpening"));
        this.setAccountManagerError(this.t("account.microsoftWaiting"));

        const done = await this.pollMicrosoftLoginStatus(start.session_id);
        if (!done?.ok) {
          this.setAccountManagerError(done?.error || this.t("error.generic"));
          return;
        }

        if (done.state) this.setState(done.state);
        if (done.account_manager) {
          this.accountManagerSelectedId = done.account_manager.selected_account_id;
          this.renderAccountManager(done.account_manager);
        }

        this.setAccountManagerError("");
        this.toast(done.message || this.t("account.microsoftAdded"));
      } catch (error) {
        this.setAccountManagerError(error?.message || String(error));
      } finally {
        button.disabled = false;
        button.textContent = previousText;
      }
    },

    async pollMicrosoftLoginStatus(sessionId) {
      const started = Date.now();
      while (Date.now() - started < 305000) {
        await new Promise(resolve => setTimeout(resolve, 1200));
        const status = await window.SLLApi.call("get_microsoft_login_status", sessionId);

        if (!status?.ok) {
          return status || { ok: false, error: this.t("error.generic") };
        }

        if (status.status === "done") {
          return status;
        }

        if (status.status === "error") {
          return { ok: false, error: status.error || status.message || this.t("error.generic") };
        }

        if (status.message) {
          this.setAccountManagerError(status.message);
        }
      }

      return { ok: false, error: this.t("account.microsoftTimeout") };
    },

    async addOfflineAccount() {
      const input = $("#offlineAccountNameInput");
      const username = input.value.trim();
      this.setAccountManagerError("");
      if (!username) {
        this.setAccountManagerError(this.t("account.offlineName"));
        return;
      }

      const button = $("#addOfflineAccountButton");
      button.disabled = true;
      try {
        const result = await window.SLLApi.call("add_offline_account", username);
        if (!result?.ok) {
          this.setAccountManagerError(result?.error || this.t("error.generic"));
          return;
        }
        input.value = "";
        if (result.state) this.setState(result.state);
        if (result.account_manager) {
          this.accountManagerSelectedId = result.account_manager.selected_account_id;
          this.renderAccountManager(result.account_manager);
        }
        this.toast(result.message || this.t("account.savedToast"));
      } catch (error) {
        this.setAccountManagerError(error?.message || String(error));
      } finally {
        button.disabled = false;
      }
    },

    async deleteSelectedAccount() {
      if (!this.accountManagerSelectedId) return;
      if (!window.confirm(this.t("account.deleteConfirm"))) return;

      this.setAccountManagerError("");
      const button = $("#deleteAccountButton");
      button.disabled = true;
      try {
        const result = await window.SLLApi.call("delete_account", this.accountManagerSelectedId);
        if (!result?.ok) {
          this.setAccountManagerError(result?.error || this.t("error.generic"));
          return;
        }
        if (result.state) this.setState(result.state);
        if (result.account_manager) {
          this.accountManagerSelectedId = result.account_manager.selected_account_id;
          this.renderAccountManager(result.account_manager);
        }
        this.toast(result.message || this.t("account.deleted"));
      } catch (error) {
        this.setAccountManagerError(error?.message || String(error));
      } finally {
        button.disabled = false;
      }
    },

    async refreshSelectedAccount() {
      this.setAccountManagerError("");
      const button = $("#refreshAccountButton");
      button.disabled = true;
      try {
        const result = await window.SLLApi.call("refresh_selected_account");
        if (!result?.ok) {
          this.setAccountManagerError(result?.error || this.t("error.generic"));
          return;
        }
        if (result.state) this.setState(result.state);
        if (result.account_manager) {
          this.accountManagerSelectedId = result.account_manager.selected_account_id;
          this.renderAccountManager(result.account_manager);
        }
        this.toast(result.message || this.t("account.refreshed"));
      } catch (error) {
        this.setAccountManagerError(error?.message || String(error));
      } finally {
        button.disabled = false;
      }
    },

    setAccountManagerError(message) {
      const box = $("#accountManagerError");
      box.textContent = message ? this.localizeMessage(message) : "";
      box.classList.toggle("hidden", !message);
    },

    async openInstanceEditor(instanceId = "") {
      this.closeMenus();
      this.hideContextMenu();
      this.setEditorError("");

      const result = await window.SLLApi.call("get_instance_editor_data", instanceId);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      const instance = result.instance || {};
      this.editorMode = result.mode || (instanceId ? "edit" : "create");
      this.editorInstanceId = instance.id || "";

      $("#instanceEditorId").value = this.editorInstanceId;
      $("#instanceNameInput").value = instance.name || "";
      $("#instanceMinecraftInput").value = instance.minecraft_version || "";
      $("#instanceVersionTypeSelect").value = instance.version_type || "release";
      $("#instanceLoaderSelect").value = instance.loader || "vanilla";
      $("#instanceLoaderVersionInput").value = instance.loader_version || "";
      $("#instanceJavaPresetSelect").value = instance.java_preset || "auto";
      $("#instanceJavaPathInput").value = instance.java_executable || "";

      const locked = Boolean(instance.locked || instance.official);
      this.editorLocked = locked;
      $("#instanceEditorTitle").textContent = this.t(
        this.editorMode === "create" ? "editor.createTitle" : "editor.editTitle"
      );
      $("#instanceLockedNote").classList.toggle("hidden", !locked);
      $("#deleteInstanceButton").classList.toggle("hidden", this.editorMode !== "edit");
      $("#deleteFilesRow").classList.add("hidden");
      $("#deleteInstanceFiles").checked = true;

      for (const element of [
        $("#instanceNameInput"),
        $("#instanceMinecraftInput"),
        $("#instanceVersionTypeSelect"),
        $("#instanceLoaderSelect"),
        $("#instanceLoaderVersionInput"),
        $("#loadMinecraftVersionsButton"),
        $("#loadLoaderVersionsButton")
      ]) {
        element.disabled = locked;
      }

      $("#minecraftVersionsNote").textContent = locked
        ? this.t("editor.lockedVersionControls")
        : this.t("editor.clickLoadVersions");
      $("#loaderVersionsNote").textContent = locked
        ? this.t("editor.lockedVersionControls")
        : "";

      this.syncInstanceEditorFields();

      // v0.6.71: version pickers open only by pressing the load buttons.
      // Opening settings must not immediately pop up extra modal windows.
      const backdrop = $("#instanceEditorBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
      setTimeout(() => {
        (locked ? $("#instanceJavaPresetSelect") : $("#instanceNameInput")).focus();
      }, 30);
    },

    async loadMinecraftVersionOptions() {
      const button = $("#loadMinecraftVersionsButton");
      const note = $("#minecraftVersionsNote");

      if (this.editorLocked || button.disabled) {
        note.textContent = this.t("editor.lockedVersionControls");
        return;
      }
      const includeSnapshots = $("#instanceVersionTypeSelect").value === "snapshot";

      button.disabled = true;
      note.textContent = this.t("picker.loading");

      try {
        const result = await window.SLLApi.call(
          "get_minecraft_version_options",
          includeSnapshots
        );
        if (!result?.ok) {
          note.textContent = result?.error || this.t("editor.versionsFailed");
          return;
        }

        const versions = result.versions || [];
        note.textContent = versions.length
          ? `${this.t("picker.loaded")}: ${versions.length}`
          : this.t("editor.noVersions");

        this.openVersionPicker(
          "minecraft",
          versions,
          this.t("picker.minecraft"),
          $("#instanceMinecraftInput").value.trim()
        );
      } catch (error) {
        note.textContent = error?.message || String(error);
      } finally {
        button.disabled = false;
      }
    },

    async loadLoaderVersionOptions() {
      const loader = $("#instanceLoaderSelect").value;
      const minecraftVersion = $("#instanceMinecraftInput").value.trim();
      const input = $("#instanceLoaderVersionInput");
      const button = $("#loadLoaderVersionsButton");
      const note = $("#loaderVersionsNote");

      if (this.editorLocked || button.disabled) {
        note.textContent = this.t("editor.lockedVersionControls");
        return;
      }

      if (loader === "vanilla") {
        input.value = "";
        note.textContent = this.t("editor.vanillaNoLoader");
        button.disabled = true;
        return;
      }

      if (!minecraftVersion) {
        note.textContent = this.t("editor.chooseMinecraftFirst");
        return;
      }

      button.disabled = true;
      note.textContent = this.t("picker.loading");

      try {
        const result = await window.SLLApi.call(
          "get_loader_version_options",
          loader,
          minecraftVersion,
          true
        );
        if (!result?.ok) {
          note.textContent = result?.error || this.t("editor.versionsFailed");
          return;
        }

        const versions = result.versions || [];
        const javaNote = result.recommended_java
          ? ` · Java ${result.recommended_java}`
          : "";
        note.textContent = versions.length
          ? `${this.t("picker.loaded")}: ${versions.length}${javaNote}`
          : this.t("editor.noVersions");

        this.openVersionPicker(
          "loader",
          versions,
          `${this.t("picker.loader")} · ${this.capitalize(loader)} ${minecraftVersion}`,
          input.value.trim()
        );
      } catch (error) {
        note.textContent = error?.message || String(error);
      } finally {
        button.disabled = false;
      }
    },

    openVersionPicker(target, values, title, currentValue = "") {
      this.versionPickerTarget = target;
      this.versionPickerValues = values || [];

      $("#versionPickerTitle").textContent = title || this.t("picker.title");
      $("#versionPickerEyebrow").textContent = this.t("picker.title");
      $("#versionPickerFilter").value = "";
      $("#versionPickerInfo").textContent = this.versionPickerValues.length
        ? `${this.t("picker.loaded")}: ${this.versionPickerValues.length}`
        : this.t("editor.noVersions");

      const backdrop = $("#versionPickerBackdrop");
      const list = $("#versionPickerList");
      // Reset scroll only when a freshly loaded picker is opened. Do not do it
      // inside renderVersionPickerList(), because that method is also used while
      // filtering and should not fight the user's manual scrolling through older
      // versions.
      if (list) list.scrollTop = 0;

      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");

      this.renderVersionPickerList(currentValue);
      requestAnimationFrame(() => {
        const freshList = $("#versionPickerList");
        if (freshList) freshList.scrollTop = 0;
      });
      setTimeout(() => $("#versionPickerFilter").focus(), 30);
    },

    closeVersionPicker() {
      const backdrop = $("#versionPickerBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
      this.versionPickerTarget = "";
      this.versionPickerValues = [];
    },

    renderVersionPickerList(currentValue = "") {
      const list = $("#versionPickerList");
      const query = $("#versionPickerFilter").value.trim().toLowerCase();
      const values = this.versionPickerValues
        .filter(value => !query || String(value).toLowerCase().includes(query))
        .slice(0, 800);

      if (!values.length) {
        list.innerHTML = `<div class="form-help">${this.t("picker.empty")}</div>`;
        return;
      }

      list.innerHTML = values.map(value => {
        const safe = this.escape(value);
        const active = value === currentValue ? " is-active" : "";
        const tag = /recommended|★/i.test(value)
          ? `<span class="version-picker__tag">★</span>`
          : "";
        return `
          <button class="version-picker__item${active}" type="button" data-version-value="${safe}">
            <span>${safe}</span>
            ${tag}
          </button>
        `;
      }).join("");

      $$("[data-version-value]", list).forEach(button => {
        button.addEventListener("click", () => this.chooseVersionFromPicker(button.dataset.versionValue));
      });
    },

    chooseVersionFromPicker(value) {
      if (this.versionPickerTarget === "minecraft") {
        $("#instanceMinecraftInput").value = value;
        this.closeVersionPicker();
        this.loadLoaderVersionOptions();
        return;
      }

      if (this.versionPickerTarget === "loader") {
        $("#instanceLoaderVersionInput").value = value;
        this.closeVersionPicker();
        return;
      }

      if (this.versionPickerTarget === "window-minecraft") {
        $("#windowSettingsMinecraft").value = value;
        this.closeVersionPicker();
        this.loadWindowLoaderVersionOptions();
        return;
      }

      if (this.versionPickerTarget === "window-loader") {
        $("#windowSettingsLoaderVersion").value = value;
        this.closeVersionPicker();
      }
    },

    closeInstanceEditor() {
      const backdrop = $("#instanceEditorBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
      this.editorLocked = false;
      this.setEditorError("");
    },

    syncInstanceEditorFields() {
      const loader = $("#instanceLoaderSelect").value;
      const loaderVersion = $("#instanceLoaderVersionInput");
      loaderVersion.disabled = this.editorLocked || $("#instanceLoaderSelect").disabled || loader === "vanilla";
      $("#loadLoaderVersionsButton").disabled =
        this.editorLocked || $("#instanceLoaderSelect").disabled || loader === "vanilla";
      $("#loadMinecraftVersionsButton").disabled = this.editorLocked || $("#instanceMinecraftInput").disabled;

      if (this.editorLocked) {
        $("#minecraftVersionsNote").textContent = this.t("editor.lockedVersionControls");
        $("#loaderVersionsNote").textContent = this.t("editor.lockedVersionControls");
      } else if (loader === "vanilla") {
        loaderVersion.value = "";
        $("#loaderVersionsNote").textContent = this.t("editor.vanillaNoLoader");
      }

      const manual = $("#instanceJavaPresetSelect").value === "manual";
      $("#instanceJavaPathField").classList.toggle("hidden", !manual);
      $("#instanceJavaPathInput").disabled = !manual;
      if (!manual) $("#instanceJavaPathInput").value = "";
    },

    instanceEditorPayload() {
      return {
        name: $("#instanceNameInput").value.trim(),
        minecraft_version: $("#instanceMinecraftInput").value.trim(),
        version_type: $("#instanceVersionTypeSelect").value,
        loader: $("#instanceLoaderSelect").value,
        loader_version: $("#instanceLoaderVersionInput").value.trim(),
        java_preset: $("#instanceJavaPresetSelect").value,
        java_executable: $("#instanceJavaPathInput").value.trim()
      };
    },

    async submitInstanceEditor(event) {
      event.preventDefault();
      this.setEditorError("");
      const saveButton = $("#instanceEditorSave");
      saveButton.disabled = true;

      try {
        const payload = this.instanceEditorPayload();
        const result = this.editorMode === "create"
          ? await window.SLLApi.call("create_instance", payload)
          : await window.SLLApi.call("update_instance", this.editorInstanceId, payload);

        if (!result?.ok) {
          this.setEditorError(result?.error || this.t("error.generic"));
          return;
        }

        if (result.state) this.setState(result.state);
        this.closeInstanceEditor();
        this.toast(this.t(this.editorMode === "create" ? "editor.created" : "editor.updated"));
      } catch (error) {
        this.setEditorError(error?.message || String(error));
      } finally {
        saveButton.disabled = false;
      }
    },

    async deleteEditedInstance() {
      if (!this.editorInstanceId) return;

      const confirmed = await this.confirmDeleteInstance(this.editorInstanceId);
      if (!confirmed) return;

      const button = $("#deleteInstanceButton");
      button.disabled = true;
      this.setEditorError("");

      try {
        const result = await window.SLLApi.call(
          "delete_instance",
          this.editorInstanceId,
          true
        );
        if (!result?.ok) {
          this.setEditorError(this.localizeMessage(result?.error || this.t("error.generic")));
          return;
        }

        if (result.state) this.setState(result.state);
        this.closeInstanceEditor();
        this.toast(
          result.files_missing
            ? this.deleteInstanceText("instanceDelete.deletedMissing")
            : this.deleteInstanceText("instanceDelete.deleted")
        );
      } catch (error) {
        this.setEditorError(error?.message || String(error));
      } finally {
        button.disabled = false;
      }
    },

    setEditorError(message) {
      const box = $("#instanceEditorError");
      box.textContent = message ? this.localizeMessage(message) : "";
      box.classList.toggle("hidden", !message);
    },

    async openClassic(plannedMessage) {
      const result = await window.SLLApi.call("open_classic_ui");
      if (result?.ok) {
        this.toast(plannedMessage ? this.t("toast.planned") : this.t("toast.classic"));

        // Classic UI is a separate process/window. Refresh a few times so
        // accounts added there can appear in the web shell without restart.
        setTimeout(() => this.refreshAppState(false), 1500);
        setTimeout(() => this.refreshAppState(false), 5000);
        setTimeout(() => this.refreshAppState(false), 12000);
      } else {
        this.toast(result?.error || this.t("error.generic"), true);
      }
    },

    showContextMenu(instanceId, x, y) {
      window.SLLState.contextInstanceId = instanceId;
      const menu = $("#contextMenu");
      const cloneButton = menu.querySelector('[data-context-action="clone"]');
      if (cloneButton) cloneButton.textContent = this.instanceToolText("instanceTools.clone");
      menu.classList.remove("hidden");
      const width = 200;
      const height = 198;
      menu.style.left = `${Math.min(x, window.innerWidth - width - 10)}px`;
      menu.style.top = `${Math.min(y, window.innerHeight - height - 10)}px`;
    },

    hideContextMenu() {
      $("#contextMenu").classList.add("hidden");
    },

    async openIconPicker(instanceId = "") {
      const id = instanceId || window.SLLState.selected_instance_id || "";
      if (!id) {
        this.toast(this.t("iconPicker.noInstance"), true);
        return;
      }

      const result = await window.SLLApi.call("get_instance_icon_pack", id);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      this.iconPickerInstanceId = id;
      this.iconPickerIcons = result.icons || [];
      this.iconPickerCategories = result.categories || ["All"];
      this.iconPickerSelected = result.selected_icon || "";
      this.iconPickerCategory = "All";
      $("#iconPickerSearch").value = "";
      const instance = (window.SLLState.instances || []).find(item => item.id === id);
      $("#iconPickerSubtitle").textContent = instance ? instance.name : "";
      this.renderIconPicker();

      const backdrop = $("#iconPickerBackdrop");
      backdrop.classList.remove("hidden");
      backdrop.setAttribute("aria-hidden", "false");
      setTimeout(() => $("#iconPickerSearch").focus(), 30);
    },

    closeIconPicker() {
      const backdrop = $("#iconPickerBackdrop");
      backdrop.classList.add("hidden");
      backdrop.setAttribute("aria-hidden", "true");
    },

    iconCategoryLabel(category) {
      if (category === "All") return this.t("iconPicker.all");
      if (category === "Official") return this.t("iconCategory.official");
      return this.t(`iconCategory.${category}`);
    },

    renderIconPicker() {
      const search = ($("#iconPickerSearch")?.value || "").trim().toLowerCase();
      const categories = this.iconPickerCategories?.length
        ? this.iconPickerCategories
        : ["All", ...Array.from(new Set(this.iconPickerIcons.map(icon => icon.category || "utility"))).sort()];
      const categoriesBox = $("#iconPickerCategories");

      categoriesBox.innerHTML = categories.map(category => `
        <button class="icon-category${category === this.iconPickerCategory ? " is-active" : ""}" type="button" data-icon-category="${this.escape(category)}">
          ${this.escape(this.iconCategoryLabel(category))}
        </button>
      `).join("");

      categoriesBox.querySelectorAll("[data-icon-category]").forEach(button => {
        button.addEventListener("click", () => {
          this.iconPickerCategory = button.dataset.iconCategory || "All";
          this.renderIconPicker();
        });
      });

      const filtered = this.iconPickerIcons.filter(icon => {
        const categoryOk = this.iconPickerCategory === "All" || icon.category === this.iconPickerCategory;
        const haystack = `${icon.id} ${icon.label} ${icon.category} ${icon.terms || ""}`.toLowerCase();
        return categoryOk && (!search || haystack.includes(search));
      });

      $("#iconPickerGrid").innerHTML = filtered.map(icon => `
        <button class="icon-choice${icon.id === this.iconPickerSelected ? " is-selected" : ""}" type="button" data-icon-id="${this.escape(icon.id)}" title="${this.escape(icon.label)}">
          <span class="icon-choice__image"><img src="${this.escape(icon.url)}" alt="" loading="lazy"></span>
          <span class="icon-choice__label">${this.escape(icon.label)}</span>
        </button>
      `).join("");

      $("#iconPickerGrid").querySelectorAll("[data-icon-id]").forEach(button => {
        button.addEventListener("click", () => this.selectIconFromPicker(button.dataset.iconId));
      });

      $("#iconPickerEmpty").classList.toggle("hidden", filtered.length > 0);
      const selected = this.iconPickerIcons.find(icon => icon.id === this.iconPickerSelected);
      $("#iconPickerSelectedLabel").textContent = selected
        ? `${this.t("iconPicker.selected")}: ${selected.label}`
        : "";
    },

    async resetInstanceIcon() {
      if (!this.iconPickerInstanceId) return;

      const result = await window.SLLApi.call("set_instance_icon", this.iconPickerInstanceId, "auto");
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      if (result.state) this.setState(result.state);
      this.toast(result.message || this.t("iconPicker.saved"));
      this.closeIconPicker();
    },

    async selectIconFromPicker(iconId) {
      if (!this.iconPickerInstanceId || !iconId) return;

      const result = await window.SLLApi.call("set_instance_icon", this.iconPickerInstanceId, iconId);
      if (!result?.ok) {
        this.toast(result?.error || this.t("error.generic"), true);
        return;
      }

      if (result.state) this.setState(result.state);
      this.iconPickerSelected = iconId;
      this.toast(result.message || this.t("iconPicker.saved"));
      this.closeIconPicker();
    },

    async cloneInstance(instanceId) {
      if (!instanceId) return;
      const result = await window.SLLApi.call("clone_instance", instanceId);
      if (!result?.ok) {
        this.toast(this.localizeMessage(result?.error || this.t("error.generic")), true);
        return;
      }

      if (result.state) this.setState(result.state);
      const name = result.cloned_instance_name || "";
      this.toast(
        name
          ? this.instanceToolText("instanceTools.clonedNamed").replace("{name}", name)
          : this.instanceToolText("instanceTools.cloned")
      );
    },

    async runContextAction(action) {
      const instanceId = window.SLLState.contextInstanceId;
      this.hideContextMenu();
      if (instanceId) await this.selectInstance(instanceId);

      if (action === "play") {
        await this.runAction("play");
      } else if (action === "folder") {
        await window.SLLApi.call("open_instance_folder", instanceId);
      } else if (action === "window") {
        await this.openInstanceWindow(instanceId);
      } else if (action === "clone") {
        await this.cloneInstance(instanceId);
      } else if (action === "icon") {
        await this.openIconPicker(instanceId);
      }
    },

    closeMenus() {
      $$(".menu.is-open").forEach(menu => menu.classList.remove("is-open"));
    },

    toggleLog() {
      const drawer = $("#logDrawer");
      const open = !drawer.classList.contains("is-open");
      drawer.classList.toggle("is-open", open);
      drawer.setAttribute("aria-hidden", String(!open));
    },

    appendLog(message) {
      if (!message) return;
      const logs = window.SLLState.logs || (window.SLLState.logs = []);
      logs.push(String(this.localizeMessage(message)));
      if (logs.length > 1000) logs.splice(0, logs.length - 1000);

      const output = $("#logOutput");
      output.textContent = logs.join("\n");
      output.scrollTop = output.scrollHeight;

      this.renderInstanceConsole();
    },

    renderInstanceConsole() {
      const output = $("#instanceConsoleOutput");
      if (!output) return;

      const logs = window.SLLState.logs || [];
      output.textContent = logs.length ? logs.join("\n") : this.t("console.empty");
      output.scrollTop = output.scrollHeight;
    },

    clearInstanceConsole() {
      window.SLLState.logs = [];
      $("#logOutput").textContent = "";
      this.renderInstanceConsole();
      this.toast(this.t("console.cleared"));
    },

    localizeMessage(message) {
      if (message === null || message === undefined) return message;
      if (window.sllTranslateMessage) return window.sllTranslateMessage(message);
      return String(message);
    },

    toast(message, error = false) {
      if (!message) return;
      message = this.localizeMessage(message);
      const toast = document.createElement("div");
      toast.className = `toast${error ? " toast--error" : ""}`;
      toast.textContent = message;
      $("#toastHost").appendChild(toast);
      setTimeout(() => toast.remove(), 3800);
    },

    receive(eventName, payload) {
      switch (eventName) {
        case "log":
          this.appendLog(payload?.message || payload);
          break;
        case "status":
          window.SLLState.status = { ...window.SLLState.status, ...payload };
          this.renderStatus(window.SLLState.status);
          this.updateActionStates();
          break;
        case "progress":
          window.SLLState.status = {
            ...window.SLLState.status,
            busy: true,
            progress: payload?.progress || 0
          };
          this.renderStatus(window.SLLState.status);
          break;
        case "done":
          window.SLLState.status = {
            ...window.SLLState.status,
            busy: false,
            progress: payload?.ok ? 1 : 0,
            message: payload?.message || this.t("status.ready"),
            error: !payload?.ok
          };
          this.renderStatus(window.SLLState.status);
          this.updateActionStates();
          this.toast(payload?.message, !payload?.ok);
          if (!payload?.ok && payload?.details) this.appendLog(payload.details);
          break;
        case "state":
          this.setState(payload);
          break;
      }
    },

    t(key) {
      return window.sllTranslate(key);
    },

    prettyTheme(theme) {
      const language = window.SLLState?.preferences?.language || "en";
      const labels = {
        en: {
          dark: "Dark",
          light: "Light",
          laconic: "Laconic",
          laconic_light: "Laconic Light",
          neon: "Neon",
          retro_future: "Retro Future"
        },
        uk: {
          dark: "Темна",
          light: "Світла",
          laconic: "Лаконічна",
          laconic_light: "Лаконічна світла",
          neon: "Неон",
          retro_future: "Ретро-футуризм"
        },
        kk: {
          dark: "Қараңғы",
          light: "Жарық",
          laconic: "Лаконикалық",
          laconic_light: "Лаконикалық жарық",
          neon: "Неон",
          retro_future: "Ретро-футуризм"
        }
      };
      if (labels[language]?.[theme]) return labels[language][theme];
      return String(theme)
        .replaceAll("_", " ")
        .replace(/\b\w/g, letter => letter.toUpperCase());
    },

    capitalize(value) {
      value = String(value || "");
      return value ? value[0].toUpperCase() + value.slice(1) : "";
    },

    formatBytes(bytes) {
      const value = Number(bytes || 0);
      if (value < 1024) return `${value} B`;
      if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
      return `${(value / 1024 / 1024).toFixed(1)} MB`;
    },

    escape(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  };

  window.StoneLightBridge = {
    receive(eventName, payload) {
      app.receive(eventName, payload);
    }
  };

  window.addEventListener("DOMContentLoaded", () => app.init());
})();
