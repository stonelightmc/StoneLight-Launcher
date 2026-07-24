# Loader version metadata

v0.6.69 changes how loader versions are listed.

The launcher now prefers official metadata sources:

```text
Forge    -> https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml
Forge    -> https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json
Fabric   -> https://meta.fabricmc.net/v2/versions/loader/{minecraft_version}
Quilt    -> https://meta.quiltmc.org/v3/versions/loader/{minecraft_version}
NeoForge -> https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml
```

`minecraft-launcher-lib` is still used for installation and as a fallback list provider.

Forge recommended builds are displayed with:

```text
★ recommended
```

The UI label is normalized before saving/installation, so the saved value remains a raw loader version.
