# Discord Video Alerts

> Baseline run38984066072 FAILED με ασφάλεια στο TikTokInfinity metadata· write SKIPPED.
> Production state κενό/αμετάβλητο,0 write attempts/baselines/queued/sent. Άδεια εξαντλήθηκε.
> MASTER/schedule OFF. Όχι νέο run/probe/write/repair. [Τρέχων οδηγός](docs/PRODUCTION_BASELINE_EL.md).


Αυτόματες ανακοινώσεις για **DayZ / Infinity** και **Milo & Mia** στο ίδιο Discord
κανάλι, με ένα υπάρχον webhook. Python + GitHub Actions, χωρίς να μένει ανοικτό
το Windows PC. Τα μηνύματα και οι ρυθμίσεις αλλάζουν από το GitHub website ή VS Code.

**Τρέχουσα κατάσταση (2026-10-17):** η μοναδική baseline προσπάθεια απέτυχε στο
strict public HTML metadata του @infinity.projectrp· production write step SKIPPED.
Νέο read-only GitHubStore επιβεβαίωσε το αρχικό κενό state/identity/hash/commit
αμετάβλητα.156 tests PASS σε Windows/Linux CI/baseline job,14 local simulations PASS.
YouTube6/14 videos επαληθεύτηκαν μόνο στη μνήμη,1 API request/~1 quota unit.
TikTok30 discovered/metadata FAILED, δεύτερο17 discovered/metadata NOT TESTED.
Κανένα committed baseline/history/queue/Discord request. [Report](docs/PRODUCTION_BASELINE_RESULTS.md).
**MASTER/media OFF, schedule disabled.** Η άδεια εξαντλήθηκε· όχι νέο run/probe/
initialization/write/repair. Νέα έγκριση απαιτείται για TikTok διάγνωση και τυχόν fix,
καθώς και ξεχωριστή νέα άδεια για επόμενη baseline προσπάθεια. Discord/monitoring/
activation παραμένουν μη εγκεκριμένα. Δεν υπάρχει συνολική production readiness.
Το TikTok παραμένει experimental· Smart Monitoring Schedule μόνο σε μελλοντικό τελικό στάδιο.
Προηγούμενα accepted reports: [canary14 checks](docs/DURABLE_CANARY_RESULTS.md),
[YouTube API two sources/2 units](docs/YOUTUBE_API_CLOUD_VALIDATION.md).

## Τι παρακολουθεί

| Πηγή ρύθμισης | Λογαριασμός |
|---|---|
| youtube_dayz | [DayZMomentsTV](https://www.youtube.com/@DayZMomentsTV) |
| youtube_milo_mia | [milo-and-mia-world](https://www.youtube.com/@milo-and-mia-world) |
| tiktok_dayz | [infinity.projectrp](https://www.tiktok.com/@infinity.projectrp) |
| tiktok_milo_mia | [milo.and.mia.world](https://www.tiktok.com/@milo.and.mia.world) |

Το ίδιο βίντεο σε YouTube και TikTok παράγει ξεχωριστές ανακοινώσεις.
Deduplication: platform + source_id + post_id. Αρχική εκτέλεση και επανενεργοποίηση
δεν στέλνουν ιστορικό περιεχόμενο. Υπάρχει ασφαλής ουρά, όριο ηλικίας 24 ωρών,
καθυστέρηση δημοσίευσης και 10 δευτερόλεπτα μεταξύ πραγματικών μηνυμάτων.

## Επόμενα βήματα μετά το cloud validation

1. Το push έχει ήδη εγκριθεί και πραγματοποιηθεί. Δες τα πραγματικά cloud results
   στο [report](docs/DEPLOYMENT_VALIDATION.md) και το [deployment guide](docs/DEPLOYMENT_EL.md).
2. Η επίσημη API λύση ανέβηκε και πέρασε το εγκεκριμένο cloud validation. Μην αφαιρείς
   identity/public checks ούτε πηγές για να εμφανιστεί πράσινο audit.
3. Το υπάρχον **DISCORD_WEBHOOK_URL** μένει στο GitHub. Δεν το αντιγράφεις εδώ,
   σε αρχείο, συνομιλία ή screenshot. Τα validation jobs δεν το λαμβάνουν.
4. Η production initialization ολοκληρώθηκε κενή. Μην την επαναλάβεις.
   Κάθε baseline-only validation ή επιπλέον state write απαιτεί νέα έγκριση.
5. Πραγματικό Discord test και MASTER/schedule activation απαιτούν ξεχωριστή έγκριση
   και επιτυχή acceptance. Τα αυθεντικά branding assets δεν έχουν δοθεί ακόμη.

Οι αλλαγές εφαρμόζονται στην επόμενη εκτέλεση μετά από commit/push. Μία τεχνική
αποτυχία πηγής δεν απενεργοποιεί τις άλλες. Το TikTok παραμένει experimental.

## Καθημερινές αλλαγές

- [config/settings.json](config/settings.json): master/πηγές, usernames, avatars,
  role, media, φίλτρα, delays, retry, logging και health thresholds.
- [config/messages](config/messages): τέσσερα αυθεντικά UTF-8 πρότυπα· κράτησε {VIDEO_URL}.
- [assets](assets): πρόσθεσε τα δικά σου αυθεντικά GIF/εικόνες· δεν έχουν δοθεί ακόμη.
- [Οδηγός λειτουργίας](docs/OPERATIONS_EL.md): πλήρης πίνακας πεδίων, manual/test,
  edit/delete, troubleshooting, restore και rollback.

## Ασφάλεια, κόστος και όρια

Τα @everyone/@here/user mentions απενεργοποιούνται. Προαιρετικό role ping επιτρέπεται
μόνο για το συγκεκριμένο configured ID. Το webhook URL δεν αποθηκεύεται σε state/logs.
Οι αβέβαιες αποστολές κρατούνται ως uncertain και δεν ξαναστέλνονται αυτόματα.
Το state branch και το Git history είναι η durable βάση, όχι cache ή προσωρινό artifact.

Ο στόχος €0/μήνα στηρίζεται σε public repository και δωρεάν standard GitHub runners.
Δεν επιτρέπονται paid APIs/υποδομές. Scheduling delays, μικρό RSS window, TikTok
blocking και αβέβαιη network delivery δεν επιτρέπουν εγγύηση άμεσης ή exactly-once
αποστολής. Τα Shorts-only/premiere φίλτρα και το Discord playback έχουν περιορισμούς.
Δες [έρευνα/συμβατότητα](docs/RESEARCH.md) και [security audit](docs/SECURITY_AUDIT.md).

## Τοπική επαλήθευση για ανάπτυξη

Python 3.12. Χρησιμοποίησε κλειδωμένες δωρεάν dependencies σε τοπικό .venv.
PowerShell, μέσα στο D:\Discord Video Alerts:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.lock
.\.venv\Scripts\python.exe scripts/check_local.py
```

Αυτό δεν στέλνει Discord μηνύματα και δεν γράφει στο GitHub. Για CLI:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m video_alerts.cli validate
.\.venv\Scripts\python.exe -m video_alerts.cli initialize --confirmation INITIALIZE
.\.venv\Scripts\python.exe -m video_alerts.cli dryrun
```

Η initialize αφορά μόνο τοπικό state όταν λείπει --github. Τοπικά δεν απαιτείται να
αποθηκεύσεις το πραγματικό webhook secret. scripts/setup_dev.py αφορά αλλαγή
dependencies και ανανέωση lock, όχι τη συνήθη αναπαραγωγή δοκιμών.

## Συνέχεια ανάπτυξης

[AGENTS.md](AGENTS.md), [CODEX_CONTEXT.md](CODEX_CONTEXT.md), [HANDOFF.md](HANDOFF.md),
[DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) και [CHANGELOG.md](CHANGELOG.md)
κρατούν απαιτήσεις, αποφάσεις, πραγματικά αποτελέσματα και ακριβή επόμενα βήματα.
Το [MASTER_REQUEST.md](docs/MASTER_REQUEST.md) είναι το αρχικό αίτημα χωρίς αλλαγές.
