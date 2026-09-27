from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceOption:
    id: str
    label: str
    gender: str


@dataclass(frozen=True)
class VisualStyleOption:
    id: str
    label: str
    description: str
    solid_color: str
    ffmpeg_filter: str


@dataclass(frozen=True)
class SubtitleStyleOption:
    id: str
    label: str
    description: str


VOICES: list[VoiceOption] = [
    VoiceOption("pt-BR-FranciscaNeural", "Francisca (feminina)", "F"),
    VoiceOption("pt-BR-AntonioNeural", "Antonio (masculino)", "M"),
    VoiceOption("pt-BR-ThalitaNeural", "Thalita (feminina)", "F"),
    VoiceOption("pt-BR-BrendaNeural", "Brenda (feminina)", "F"),
    VoiceOption("pt-BR-DonatoNeural", "Donato (masculino)", "M"),
    VoiceOption("pt-BR-FabioNeural", "Fabio (masculino)", "M"),
    VoiceOption("pt-BR-ElzaNeural", "Elza (feminina)", "F"),
    VoiceOption("pt-BR-GiovannaNeural", "Giovanna (feminina)", "F"),
]

VISUAL_STYLES: list[VisualStyleOption] = [
    VisualStyleOption(
        "realistic",
        "Filme realista",
        "Contraste suave e cores naturais",
        "0x1a1a2e",
        "eq=contrast=1.05:brightness=0.02:saturation=1.08",
    ),
    VisualStyleOption(
        "cinematic",
        "Cinematográfico",
        "Tom escuro com contraste marcado",
        "0x0d0d14",
        "eq=contrast=1.18:brightness=-0.05:saturation=0.92",
    ),
    VisualStyleOption(
        "vibrant",
        "Cores vibrantes",
        "Saturação alta para redes sociais",
        "0x12122a",
        "eq=contrast=1.08:brightness=0.03:saturation=1.35",
    ),
    VisualStyleOption(
        "minimal",
        "Minimalista",
        "Visual limpo, pouca correção",
        "0x181818",
        "",
    ),
    VisualStyleOption(
        "vintage",
        "Vintage",
        "Tom quente retrô",
        "0x1f1810",
        "eq=contrast=1.05:saturation=0.85:gamma=1.08",
    ),
    VisualStyleOption(
        "noir",
        "Preto e branco",
        "Estilo dramático monocromático",
        "0x0a0a0a",
        "hue=s=0,eq=contrast=1.12:brightness=-0.02",
    ),
]

SUBTITLE_STYLES: list[SubtitleStyleOption] = [
    SubtitleStyleOption(
        "classic",
        "Legenda clássica",
        "Blocos de texto sincronizados na parte inferior",
    ),
    SubtitleStyleOption(
        "karaoke",
        "Karaoke",
        "Palavras destacadas conforme a narração avança",
    ),
]


def get_visual_style(style_id: str) -> VisualStyleOption:
    for s in VISUAL_STYLES:
        if s.id == style_id:
            return s
    return VISUAL_STYLES[0]


def list_options_dict() -> dict:
    return {
        "voices": [
            {"id": v.id, "label": v.label, "gender": v.gender} for v in VOICES
        ],
        "visualStyles": [
            {
                "id": s.id,
                "label": s.label,
                "description": s.description,
            }
            for s in VISUAL_STYLES
        ],
        "subtitleStyles": [
            {"id": s.id, "label": s.label, "description": s.description}
            for s in SUBTITLE_STYLES
        ],
        "sceneMediaModes": [
            {"id": "video", "label": "Clipes de vídeo"},
            {"id": "photo", "label": "Imagens"},
            {"id": "mixed", "label": "Misto (vídeo + fotos)"},
        ],
    }
