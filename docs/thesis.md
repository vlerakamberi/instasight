# InstaSight: Një Sistem Inteligjent për Analizën e të Dhënave dhe Strategjinë e Rritjes në Instagram për Bizneset e Vogla

### Punim Diplome (Projekt Kapstoni)

**Studim rasti:** Klinika dentare Dental-B (@dentalb_ku), Kumanovë, Maqedoni e Veriut

---

## Abstrakt

Ky punim paraqet InstaSight, një sistem softuerik i ndërtuar në gjuhën Python që transformon të dhënat e papërpunuara të Instagram Graph API në udhëzime konkrete dhe të bazuara në të dhëna për rritjen e bizneseve të vogla. Sistemi integron sinkronizimin e të dhënave, llogaritjen e metrikave të performancës, gjenerimin e përmbajtjes nëpërmjet inteligjencës artificiale (Anthropic Claude), monitorimin e automatizuar ditor dhe një panel ndërveprues të ndërtuar me Streamlit. Përmes studimit të rastit të klinikës dentare Dental-B, punimi demonstron se si një vegël e aksesueshme mund të ofrojë cilësinë e analizës që zakonisht ofron një konsulent profesionist marketingu, por me kosto thelbësisht më të ulët. Rezultatet tregojnë identifikimin e problemeve kritike — një normë angazhimi prej 1.68% kundrejt potencialit 4-6%, një ndërprerje publikimi prej 685 ditësh, dhe mungesë të plotë të formatit Reels — së bashku me rekomandime të aplikueshme menjëherë.

**Fjalë kyçe:** Instagram Graph API, analizë e të dhënave, inteligjencë artificiale, marketing dixhital, monitorim i automatizuar, biznese të vogla.

---

## Kapitulli 1 — Hyrje (Introduction)

Marketingu dixhital në platformat e mediave sociale është bërë një faktor vendimtar për mbijetesën dhe rritjen e bizneseve të vogla dhe të mesme. Instagram, në veçanti, përfaqëson një kanal kryesor për ndërtimin e besimit dhe arritjen e klientëve të rinj, sidomos në sektorë si ai i shërbimeve shëndetësore ku besimi personal është faktori parësor i konvertimit. Megjithatë, ekziston një hendek kritik për bizneset e vogla në tregun shqipfolës (Maqedoni e Veriut, Kosovë, Shqipëri dhe diaspora): konsulentët profesionistë të marketingut dixhital tarifojnë midis 500 dhe 2.000 euro në muaj, një kosto e papërballueshme për një klinikë dentare lokale me më pak se 1.000 ndjekës.

Veglat gjenerike të inteligjencës artificiale, si ChatGPT, nuk e zgjidhin këtë problem, sepse atyre u mungon qasja në të dhënat reale të biznesit — performanca historike, modelet specifike të llogarisë dhe metrikat e angazhimit. Si rrjedhojë, këshillat e tyre mbeten të përgjithshme dhe të pazbatueshme në kontekstin konkret të biznesit.

InstaSight u konceptua pikërisht për ta mbushur këtë hendek. Sistemi ofron cilësinë e një analize të bazuar në të dhëna që do ta jepte një marketer i lartë i rritjes, por të mbështetur tërësisht në të dhënat reale të vetë biznesit, të nxjerra drejtpërdrejt nga Instagram Graph API. Qëllimi kryesor i punimit është të dizajnojë, implementojë dhe vlerësojë një sistem që: (1) sinkronizon dhe ruan të dhënat e Instagramit në një bazë të dhënash lokale; (2) llogarit metrika kuptimplota të performancës; (3) gjeneron diagnozë dhe strategji përmes IA-së të bazuar në kontekst real; (4) monitoron automatikisht llogarinë dhe njofton përmes email-it; dhe (5) i paraqet të gjitha këto në një ndërfaqe vizuale të kuptueshme.

Objektivat specifikë të hulumtimit përfshijnë vërtetimin e hipotezës se një sistem i automatizuar mund të zëvendësojë analizën manuale të një konsulenti për pjesën diagnostikuese, duke ruajtur saktësinë dhe specifikën. Studimi i rastit me klinikën Dental-B (@dentalb_ku), me 999 ndjekës, shërben si terreni empirik për të vlerësuar vlerën praktike të sistemit. Punimi është i strukturuar në gjashtë kapituj që ndjekin metodologjinë standarde akademike, nga rishikimi i literaturës deri te diskutimi i rezultateve dhe konkluzionet.

---

## Kapitulli 2 — Rishikimi i Literaturës (Literature Review)

Literatura mbi marketingun në mediat sociale dhe analizën e të dhënave ofron një kornizë të gjerë teorike për këtë punim. Studimet e angazhimit (engagement) tregojnë se norma mesatare e angazhimit në Instagram ka rënë ndjeshëm gjatë viteve, duke arritur vlera prej 0.48-0.50% sipas raporteve të Social Insider për vitin 2026. Megjithatë, llogaritë e vogla të kategorisë "nano" (1.000-10.000 ndjekës) shfaqin norma dukshëm më të larta, midis 4% dhe 6%, për shkak të një lidhjeje më të ngushtë dhe autentike me audiencën. Ky dallim është thelbësor për të kuptuar potencialin real të një biznesi si Dental-B.

Hulumtimet mbi formatet e përmbajtjes konfirmojnë se Reels-at gjenerojnë rreth 30% më shumë shtrirje (reach) se postimet statike, ndërsa përmbajtja "para/pas" (before/after) — veçanërisht relevante për sektorin dentar — arrin norma angazhimi deri në 5.2%. Postimet edukative në formë karuseli nxisin ruajtjet (saves), të cilat janë një sinjal i fortë për algoritmin e shpërndarjes. Kjo literaturë e specializuar formon bazën e të dhënave krahasuese (benchmark) të integruar në sistem.

Në fushën e algoritmeve të shpërndarjes, studimet tregojnë se Instagram penalizon llogaritë joaktive: frekuenca e publikimit prej 3-5 herë në javë shoqërohet me rritje deri në tri herë më të shpejtë krahasuar me llogaritë që publikojnë një herë në javë. Ky konstatim teorik shpjegon drejtpërdrejt problemin e Dental-B, që publikon vetëm 0.07 herë në javë.

Sa i përket inteligjencës artificiale gjeneruese, modelet e mëdha gjuhësore (LLM) si Claude i Anthropic-ut kanë treguar aftësi të jashtëzakonshme në gjenerimin e tekstit kontekstual. Megjithatë, literatura mbi "grounding" (mbështetjen në fakte) thekson se cilësia e daljes varet tërësisht nga cilësia e kontekstit hyrës. Pa të dhëna specifike, modeli prodhon këshilla gjenerike. Ky parim teorik justifikon vendimin e dizajnit në InstaSight për t'i ushqyer modelit vetëm metrika reale të nxjerra nga baza e të dhënave.

Më në fund, konteksti i tregut shqipfolës mbetet i nënhulumtuar në literaturën akademike. Të dhënat tregojnë se turizmi dentar në Shqipëri është rritur 400% që nga viti 2020, me mbi 80.000 pacientë në vitin 2024, ndërsa diaspora shqiptare kërkon në mënyrë aktive shërbime në gjuhën amtare. Ky hendek në literaturë e bën punimin një kontribut origjinal për një treg specifik dhe të pashfrytëzuar mjaftueshëm.

---

## Kapitulli 3 — Metodologjia (Methodology)

Metodologjia e këtij punimi ndjek një qasje të zhvillimit të orientuar nga dizajni (design-oriented research), e kombinuar me një studim rasti të vetëm për validim empirik. Sistemi u ndërtua në mënyrë modulare, ku secili komponent ka një përgjegjësi të qartë dhe të izoluar, duke lehtësuar testimin dhe mirëmbajtjen.

Arkitektura e sistemit u organizua në shtresa të dallueshme. Shtresa e integrimit me API-në (`app/api/meta_client.py`) komunikon me Instagram Graph API përmes versionit v18.0, duke përdorur endpoint-e specifike për profilin, mediat e fundit dhe metrikat e secilit postim. Për qëndrueshmëri, të gjitha thirrjet kalojnë përmes një mekanizmi riprovimi (`run_with_retry`) me strategji backoff eksponencial prej tri përpjekjesh; në rast gabimi HTTP 400, sistemi kthen vlera zero në vend që të dështojë i tëri.

Shtresa e ruajtjes së të dhënave përdor SQLite si bazë të dhënash lokale (`data/instasight.db`), me pesë tabela kryesore: `accounts`, `posts`, `insights`, `performance_snapshots` dhe `alerts`. Skema përdor kufizime të çelësave të huaj dhe indekse për të optimizuar pyetjet. Sinkronizimi (`sync_account_data`) zbaton një logjikë "upsert" për llogaritë dhe postimet, ndërsa për metrikat ruan një fotografi (snapshot) të re në çdo ekzekutim, duke mundësuar analizën historike.

Llogaritja e metrikave (`metrics.py`) zbaton formulën standarde të normës së angazhimit: `(pëlqime + komente) / ndjekës × 100`. Mbi këtë bazë, moduli `analysis.py` agregon metrikat dhe gjeneron vëzhgime të lexueshme, ndërsa `report_builder.py` i strukturon ato në një kontekst tekstual të gatshëm për modelin gjuhësor.

Komponenti i inteligjencës artificiale u ndërtua mbi modelin `claude-sonnet-4-6`. Dy veçori plotësuese u dizajnuan qëllimisht: "Performance Advisor" për një diagnozë të shkurtër dhe të fokusuar për përdorim të rregullt, dhe "AI Strategy" për një auditim të thellë një herë. Të dyja mbështeten ekskluzivisht në të dhënat reale, duke shtuar një bllok të dhënash krahasuese të verifikuara (`benchmarks.py`). Dy veçoritë e para përdorin transmetim në kohë reale (streaming) për përvojë më të mirë përdoruesi.

Monitorimi i automatizuar (`monitoring.py` dhe `scheduler.py`) kap fotografi ditore dhe gjeneron sinjalizime kur angazhimi bie mbi 20%, kur ka mungesë publikimi mbi 7 ditë, ose kur ndodh një rritje mbi 30%. Njoftimet dërgohen përmes Gmail SMTP. Vlerësimi i sistemit u krye duke e aplikuar atë mbi të dhënat reale të Dental-B dhe duke krahasuar gjetjet me të dhënat krahasuese të industrisë.

---

## Kapitulli 4 — Implementimi (Implementation)

Implementimi i InstaSight u realizua tërësisht në Python, duke shfrytëzuar një grup bibliotekash të specializuara: `requests` për komunikimin me API-në, `pandas` për përpunimin e të dhënave, `anthropic` për inteligjencën artificiale, `streamlit` dhe `plotly` për vizualizimin, `schedule` për planifikimin dhe `python-dotenv` për menaxhimin e konfigurimit. Kredencialet ndjeshëm ruhen në një skedar `.env` dhe ngarkohen përmes funksionit `load_settings()`, i cili validon praninë e çelësave të domosdoshëm.

Rrjedha e të dhënave fillon me klasën `MetaClient`, e cila nxjerr informacionin e profilit (emri i përdoruesit, numri i ndjekësve, numri i mediave), mediat e fundit (deri në 20 postime) dhe metrikat për secilin postim. Gjatë zhvillimit u hasën sfida reale me lejet e API-së: kërkesat fillestare për fushat `biography` dhe disa metrika të caktuara dështonin me gabim 400. Zgjidhja konsistoi në një logjikë rënëse (fallback) ku sistemi fillimisht provon fushat e plota dhe, nëse dështon, kalon në një grup më minimal fushash. Po ashtu, metrikat e postimeve u morën përmes fushave të objektit media (`like_count`, `comments_count`) në vend të endpoint-it `/insights`, i cili kishte emra metrikash të papërputhshëm me versionin v18.0.

Pas sinkronizimit, funksioni `sync_account_data()` shkruan të dhënat në SQLite, duke regjistruar progresin në `data/app.log` përmes një loguesi qendror. Moduli i metrikave llogarit normën mesatare të angazhimit, postimet me performancën më të lartë, frekuencën e publikimit, ditën më të mirë dhe performancën sipas tipit të përmbajtjes.

Komponenti më i rëndësishëm konceptual është `build_prompt_context()`, i cili gjeneron një kontekst tekstual të pasur me të dhëna reale: numrin e ndjekësve, normën e angazhimit me formulën përkatëse, frekuencën e publikimit, tri postimet kryesore me tekstet dhe datat e tyre, kronologjinë e publikimit me hendeqet midis postimeve, dhe ndarjen sipas tipit të medias. Ky kontekst i ushqehet modelit Claude së bashku me një "system prompt" që përcakton personin e ekspertit dhe rregullat strikte për të mos shpikur numra.

Paneli i ndërtuar me Streamlit (`streamlit_app.py`) organizohet në pesë faqe: Overview, Post Analysis, Trends, AI Strategy dhe Performance Advisor. Faqja kryesore shfaq katër karta KPI, grafikë të angazhimit dhe një tabelë të detajuar. Planifikuesi në sfond nis automatikisht në ngarkesën e parë të aplikacionit, ndërsa skedari i pavarur `scripts/run_monitoring.py` mundëson ekzekutimin e monitorimit edhe pa hapur panelin — i konfiguruar përmes Windows Task Scheduler për t'u ekzekutuar çdo ditë në orën 08:00.

---

## Kapitulli 5 — Rezultatet dhe Diskutimi (Results and Discussion)

Aplikimi i sistemit InstaSight mbi llogarinë reale të klinikës Dental-B (@dentalb_ku) prodhoi gjetje konkrete dhe domethënëse, të cilat ilustrojnë vlerën praktike të qasjes së bazuar në të dhëna. Tabela e mëposhtme përmbledh metrikat kryesore të identifikuara nga sistemi në krahasim me të dhënat krahasuese të industrisë:

| Metrika | Vlera | Standardi (benchmark) | Statusi |
|---------|-------|------------------------|---------|
| Norma mesatare e angazhimit | 1.68% | 4-6% (llogari nano) | Nën potencial |
| Postime në javë | 0.07 | 3-5/javë | Hendek kritik |
| Ndërprerja më e gjatë e publikimit | 685 ditë | — | Dormancë e llogarisë |
| Reels të publikuara | 0 | 40% e përzierjes së përmbajtjes | Format që mungon |
| Komente për postim | ~0 | 3-8 | Audiencë pasive |

Diagnoza e gjeneruar nga "Performance Advisor" ishte veçanërisht e thellë: sistemi konstatoi se Dental-B zotëron një audiencë funksionale — norma prej 1.68% dëshmon se njerëzit reagojnë kur përmbajtja shfaqet — por publikon aq rrallë sa algoritmi i Instagramit ka ndaluar shpërndarjen e përmbajtjes. Ky është një dallim i hollë por kritik: problemi nuk është mungesa e interesit të audiencës, por joaktiviteti i llogarisë. Ndërprerja prej 685 ditësh përbën shkakun rrënjësor të penalizimit algoritmik, një gjetje që përputhet plotësisht me literaturën e shqyrtuar në Kapitullin 2.

Veçoria "AI Strategy" zbuloi një gabim strategjik që nuk do të ishte i dukshëm pa analizë specifike: hashtag-ët ekzistues synonin audienca anglishtfolëse dhe dentistë në Turqi, në vend të folësve shqip në rajon. Ky gabim u kushtonte llogarisë shtrirje organike të çmuar. Sistemi ofroi një kornizë të plotë hashtag-ësh specifikë për tregun dentar shqiptar, duke kombinuar tagë lokalë, të nishës dhe të komunitetit.

Diskutimi i këtyre rezultateve nxjerr në pah një mësim qendror të dizajnit: vlera reale e sistemit nuk qëndron në gjenerimin e përmbajtjes (një mall i zakonshëm që e ofrojnë ChatGPT, Canva, Buffer dhe Later), por në diagnozën specifike. Pronari i biznesit nuk ka nevojë për një tekst tjetër postimi — ai ka nevojë të kuptojë pse angazhimi i tij është 1.68% në vend të 4-6% dhe çfarë veprimesh konkrete duhet të ndërmarrë.

Monitorimi i automatizuar dëshmoi qëndrueshmërinë e sistemit duke kapur fotografi ditore në mënyrë të pavarur nga paneli. Megjithatë, një kufizim i rëndësishëm është se analiza historike e tendencave kërkon të paktën dy fotografi (snapshot), pra sistemi bëhet plotësisht i dobishëm vetëm pas disa ditësh grumbullimi të të dhënave. Një kufizim tjetër është varësia nga lejet e API-së, të cilat mund të kufizojnë disa metrika si shtrirja dhe ruajtjet.

---

## Kapitulli 6 — Konkluzionet (Conclusions)

Ky punim demonstroi me sukses se një sistem softuerik i aksesueshëm mund të ofrojë analizë marketingu të bazuar në të dhëna me cilësi profesionale për bizneset e vogla, duke mbushur një hendek real në tregun shqipfolës. InstaSight integroi në mënyrë koherente sinkronizimin e të dhënave nga Instagram Graph API, llogaritjen e metrikave të performancës, gjenerimin e diagnozës dhe strategjisë përmes inteligjencës artificiale të mbështetur në kontekst real, monitorimin e automatizuar dhe vizualizimin ndërveprues.

Studimi i rastit me klinikën Dental-B vërtetoi hipotezën qendrore: sistemi zëvendësoi nevojën për një konsulent të paguar marketingu për pjesën e analizës së performancës. Konkretisht, InstaSight ofroi një kornizë të plotë hashtag-ësh specifikë për tregun dentar shqiptar, identifikoi një ndërprerje publikimi prej 685 ditësh që shkaktonte penalizim algoritmik, prodhoi një plan aktivizimi 30-ditor të bazuar në të dhënat reale historike të llogarisë, dhe vendosi një monitorim ditor të automatizuar me sinjalizime përmes email-it. Të gjitha këto rezultate ishin specifike për biznesin e analizuar, duke vërtetuar parimin se cilësia e daljes së IA-së varet nga mbështetja në të dhëna reale.

Kontributi kryesor i punimit qëndron në kombinimin e tri elementeve që rrallë bashkohen: integrimi i të dhënave reale të biznesit, mbështetja strikte e modelit gjuhësor në këto të dhëna, dhe fokusi në diagnozë në vend të prodhimit gjenerik të përmbajtjes. Vendimi i dizajnit për të ndarë "Performance Advisor" nga "AI Strategy" u tregua i vlefshëm, duke u përshtatur me dy nevoja të dallueshme përdorimi.

Sa i përket punës së ardhshme, ekzistojnë disa drejtime premtuese. Së pari, sistemi mund të zgjerohet për të mbështetur disa llogari njëkohësisht, duke kaluar nga një `ACCOUNT_ID` i fiksuar në një model shumë-përdoruesh. Së dyti, integrimi me API-të e tjera (Facebook, TikTok) do të ofronte një pamje më të plotë të pranisë dixhitale. Së treti, mbledhja afatgjatë e fotografive të performancës do të mundësonte modele parashikuese të rritjes nëpërmjet mësimit të makinës. Së fundi, gjenerimi i drejtpërdrejtë i përmbajtjes vizuale (imazhe para/pas, Reels) do ta plotësonte ciklin nga diagnoza te ekzekutimi.

Përfundimisht, InstaSight përfaqëson një hap konkret drejt demokratizimit të marketingut dixhital të bazuar në të dhëna, duke vënë në dispozicion të bizneseve të vogla mjete që dikur ishin ekskluzivitet i konsulentëve të shtrenjtë.

---

## Referencat

1. Social Insider (2026). *Instagram Engagement Rate Benchmarks Report*.
2. Dokumentacioni Teknik i Projektit InstaSight (`docs/TECHNICAL_DOCUMENTATION.md`).
3. Meta for Developers. *Instagram Graph API Documentation (v18.0)*.
4. Anthropic. *Claude API Documentation* (model `claude-sonnet-4-6`).
5. Të dhënat reale të llogarisë Dental-B (@dentalb_ku), qershor 2026.
