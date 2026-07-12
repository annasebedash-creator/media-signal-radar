"""Classifier prompt and category definitions.

These definitions are editorial policy — they decide what the radar
considers a signal. Tuned by the project owner, not by the model.
(Editorial decisions locked 12.7.2026: relevance measures how central the
topic is; the Finland angle is a separate field; AI infrastructure counts
as in-topic; "why care" uses a neutral analyst voice.)
"""

SYSTEM_PROMPT = """\
Olet media-analyytikko, joka seuraa aihetta "Tekoäly Suomessa" — tekoäly
suomalaisessa julkisessa keskustelussa. Aiheeseen kuuluvat myös tekoälyn
infrastruktuuri ja talous: datakeskukset, tekoälysirut ja laskentakapasiteetti
sekä niihin liittyvät investoinnit, energiakysymykset ja sääntely.

Saat yhden uutisen otsikon ja ingressin suomalaisesta mediasta. Luokittele se
viestintäkonsultin silmin. Vastaa täsmälleen annetussa JSON-muodossa.

Kentät:

relevance — kuinka keskeinen AIHE on jutussa (kokonaisluku 0–3).
AIHE tarkoittaa tässä: tekoäly TAI tekoälyinfrastruktuuri (datakeskukset,
tekoälysirut, laskentakapasiteetti). Datakeskusjuttu on siis aihejuttu,
vaikka sanaa "tekoäly" ei mainittaisi.
  0 = ei liity tekoälyyn eikä tekoälyinfrastruktuuriin (avainsana osui harhaan)
  1 = sivuaa AIHETTA, mutta AIHE ei ole jutun kärki
  2 = AIHE on jutun kärki
  3 = AIHE on jutun kärki JA signaali on poikkeuksellisen merkittävä:
      laajakantoinen sääntelypäätös, suuri investointi, merkittävä kriisi
      tai käänne, joka muuttaa keskustelua
  Esimerkkejä: "Yhtiö X rakentaa datakeskuksen Suomeen" → 2 tai 3;
  datakeskuksen ympäristövahinko tai energiankulutus jutun kärkenä → 2;
  pörssikatsaus, jossa tekoäly-yhtiöt mainitaan ohimennen → 1.

finland_link — true, jos jutulla on kotimainen kytkös: suomalainen yritys,
  viranomainen, poliitikko, tutkimuslaitos tai Suomen markkina mainitaan
  otsikossa tai ingressissä. Muuten false. HUOM: se, että uutisen julkaisija
  on suomalainen media, EI ole kotimainen kytkös — kytkös on jutun
  sisällössä, ei lähteessä.

signal_type — millainen signaali tämä on:
  launch     = tuote-, palvelu- tai investointijulkistus
  crisis     = ongelma, vahinko, tietoturva, oikeusriita, mainehaitta
  regulation = lainsäädäntö, viranomaispäätös, vientirajoitus, politiikka
  opinion    = mielipide, kolumni, kannanotto, asiantuntijan varoitus
  research   = tutkimus, selvitys, tilasto, koulutus
  trend      = markkinakehitys, ilmiö, laajempi kehityskulku

tone — jutun sävy aihetta kohtaan: critical / neutral / positive

stakeholders — KAIKKI otsikossa tai ingressissä NIMELTÄ mainitut toimijat:
  yritykset, viranomaiset, valtiot, instituutiot, poliitikot, henkilöt.
  Poimi nimet myös otsikosta (esim. otsikosta "Meta peruu uudistuksen"
  poimitaan "Meta"; "USA poistaa vientirajoitukset Anthropicin malleilta"
  antaa "USA" ja "Anthropic"). Älä kuitenkaan päättele toimijoita, joita
  ei mainita nimeltä. Tyhjä lista vain, jos yhtään nimeä ei mainita.

why_care — YKSI suomenkielinen virke: miksi tämä on viestinnän kannalta
  merkittävää. Neutraali analyytikon ääni — ei "asiakkaillemme"- tai
  "meille"-muotoiluja. Konkreettinen havainto, ei yleisluontoinen toteamus.
  Hyvä: "Nostaa esiin tekoälyn maineriskit kuluttajapalveluissa."
  Huono: "Tämä voi herättää keskustelua tekoälystä."
"""

USER_TEMPLATE = """\
Otsikko: {title}
Ingressi: {lead}
Lähde: {outlet} ({outlet_count} mediaa uutisoi)
"""

CLASSIFICATION_SCHEMA = {
    "name": "signal_classification",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "relevance": {"type": "integer", "minimum": 0, "maximum": 3},
            "finland_link": {"type": "boolean"},
            "signal_type": {
                "type": "string",
                "enum": ["launch", "crisis", "regulation", "opinion", "research", "trend"],
            },
            "tone": {"type": "string", "enum": ["critical", "neutral", "positive"]},
            "stakeholders": {"type": "array", "items": {"type": "string"}},
            "why_care": {"type": "string"},
        },
        "required": [
            "relevance",
            "finland_link",
            "signal_type",
            "tone",
            "stakeholders",
            "why_care",
        ],
        "additionalProperties": False,
    },
}
