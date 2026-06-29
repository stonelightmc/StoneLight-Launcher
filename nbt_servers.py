import shutil
import struct
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


@dataclass
class NbtTag:
    type_id: int
    value: object


@dataclass
class NbtList:
    element_type: int
    items: list


def _read_exact(f: BinaryIO, size: int) -> bytes:
    data = f.read(size)
    if len(data) != size:
        raise EOFError("Unexpected end of NBT file")
    return data


def _read_string(f: BinaryIO) -> str:
    length = struct.unpack(">H", _read_exact(f, 2))[0]
    return _read_exact(f, length).decode("utf-8")


def _write_string(f: BinaryIO, value: str):
    data = value.encode("utf-8")
    f.write(struct.pack(">H", len(data)))
    f.write(data)


def _read_payload(f: BinaryIO, type_id: int):
    if type_id == TAG_BYTE:
        return struct.unpack(">b", _read_exact(f, 1))[0]
    if type_id == TAG_SHORT:
        return struct.unpack(">h", _read_exact(f, 2))[0]
    if type_id == TAG_INT:
        return struct.unpack(">i", _read_exact(f, 4))[0]
    if type_id == TAG_LONG:
        return struct.unpack(">q", _read_exact(f, 8))[0]
    if type_id == TAG_FLOAT:
        return struct.unpack(">f", _read_exact(f, 4))[0]
    if type_id == TAG_DOUBLE:
        return struct.unpack(">d", _read_exact(f, 8))[0]
    if type_id == TAG_BYTE_ARRAY:
        length = struct.unpack(">i", _read_exact(f, 4))[0]
        return _read_exact(f, length)
    if type_id == TAG_STRING:
        return _read_string(f)
    if type_id == TAG_LIST:
        element_type = struct.unpack(">b", _read_exact(f, 1))[0]
        length = struct.unpack(">i", _read_exact(f, 4))[0]
        return NbtList(element_type, [NbtTag(element_type, _read_payload(f, element_type)) for _ in range(length)])
    if type_id == TAG_COMPOUND:
        compound = OrderedDict()
        while True:
            child_type = struct.unpack(">B", _read_exact(f, 1))[0]
            if child_type == TAG_END:
                break
            name = _read_string(f)
            compound[name] = NbtTag(child_type, _read_payload(f, child_type))
        return compound
    if type_id == TAG_INT_ARRAY:
        length = struct.unpack(">i", _read_exact(f, 4))[0]
        return [struct.unpack(">i", _read_exact(f, 4))[0] for _ in range(length)]
    if type_id == TAG_LONG_ARRAY:
        length = struct.unpack(">i", _read_exact(f, 4))[0]
        return [struct.unpack(">q", _read_exact(f, 8))[0] for _ in range(length)]
    raise ValueError(f"Unsupported NBT tag type: {type_id}")


def _write_payload(f: BinaryIO, tag: NbtTag):
    type_id = tag.type_id
    value = tag.value

    if type_id == TAG_BYTE:
        f.write(struct.pack(">b", int(value)))
    elif type_id == TAG_SHORT:
        f.write(struct.pack(">h", int(value)))
    elif type_id == TAG_INT:
        f.write(struct.pack(">i", int(value)))
    elif type_id == TAG_LONG:
        f.write(struct.pack(">q", int(value)))
    elif type_id == TAG_FLOAT:
        f.write(struct.pack(">f", float(value)))
    elif type_id == TAG_DOUBLE:
        f.write(struct.pack(">d", float(value)))
    elif type_id == TAG_BYTE_ARRAY:
        data = bytes(value)
        f.write(struct.pack(">i", len(data)))
        f.write(data)
    elif type_id == TAG_STRING:
        _write_string(f, str(value))
    elif type_id == TAG_LIST:
        nbt_list: NbtList = value
        f.write(struct.pack(">b", nbt_list.element_type))
        f.write(struct.pack(">i", len(nbt_list.items)))
        for item in nbt_list.items:
            if item.type_id != nbt_list.element_type:
                item = NbtTag(nbt_list.element_type, item.value)
            _write_payload(f, item)
    elif type_id == TAG_COMPOUND:
        for name, child in value.items():
            f.write(struct.pack(">B", child.type_id))
            _write_string(f, name)
            _write_payload(f, child)
        f.write(struct.pack(">B", TAG_END))
    elif type_id == TAG_INT_ARRAY:
        f.write(struct.pack(">i", len(value)))
        for item in value:
            f.write(struct.pack(">i", int(item)))
    elif type_id == TAG_LONG_ARRAY:
        f.write(struct.pack(">i", len(value)))
        for item in value:
            f.write(struct.pack(">q", int(item)))
    else:
        raise ValueError(f"Unsupported NBT tag type: {type_id}")


def read_nbt(path: Path) -> tuple[str, NbtTag]:
    with Path(path).open("rb") as f:
        root_type = struct.unpack(">B", _read_exact(f, 1))[0]
        if root_type != TAG_COMPOUND:
            raise ValueError(f"Root tag must be TAG_Compound, got {root_type}")
        root_name = _read_string(f)
        root_value = _read_payload(f, root_type)
        return root_name, NbtTag(root_type, root_value)


def write_nbt(path: Path, root_name: str, root_tag: NbtTag):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    with tmp.open("wb") as f:
        f.write(struct.pack(">B", TAG_COMPOUND))
        _write_string(f, root_name)
        _write_payload(f, root_tag)

    tmp.replace(path)


def make_root() -> tuple[str, NbtTag]:
    return "", NbtTag(TAG_COMPOUND, OrderedDict())


def make_server_compound(name: str, ip: str) -> NbtTag:
    return NbtTag(TAG_COMPOUND, OrderedDict([
        ("name", NbtTag(TAG_STRING, name)),
        ("ip", NbtTag(TAG_STRING, ip)),
    ]))


def get_string_from_compound(compound_tag: NbtTag, key: str) -> str:
    if compound_tag.type_id != TAG_COMPOUND:
        return ""
    child = compound_tag.value.get(key)
    if not child or child.type_id != TAG_STRING:
        return ""
    return str(child.value)


def ensure_server_in_list(game_dir: Path, server_name: str, server_ip: str, log=None) -> bool:
    game_dir = Path(game_dir)
    servers_path = game_dir / "servers.dat"
    game_dir.mkdir(parents=True, exist_ok=True)

    def emit(message: str):
        if log:
            log(message)

    if servers_path.exists():
        try:
            root_name, root_tag = read_nbt(servers_path)
        except Exception as exc:
            backup = game_dir / f"servers.dat.bak_{time.strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(servers_path, backup)
            emit(f"Не удалось прочитать servers.dat, создана резервная копия: {backup.name}. Причина: {exc}")
            root_name, root_tag = make_root()
    else:
        root_name, root_tag = make_root()

    if root_tag.type_id != TAG_COMPOUND:
        root_name, root_tag = make_root()

    root = root_tag.value
    servers_tag = root.get("servers")

    if not servers_tag or servers_tag.type_id != TAG_LIST or servers_tag.value.element_type != TAG_COMPOUND:
        servers_tag = NbtTag(TAG_LIST, NbtList(TAG_COMPOUND, []))
        root["servers"] = servers_tag

    servers_list: NbtList = servers_tag.value
    normalized_target_ip = server_ip.strip().lower()

    for item in servers_list.items:
        existing_ip = get_string_from_compound(item, "ip").strip().lower()
        if existing_ip == normalized_target_ip:
            emit(f"Сервер уже есть в списке Minecraft: {server_ip}")
            return False

    servers_list.items.insert(0, make_server_compound(server_name, server_ip))
    write_nbt(servers_path, root_name, root_tag)
    emit(f"Сервер добавлен в список Minecraft: {server_name} / {server_ip}")
    return True
