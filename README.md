# Discord Video Alerts

> Production initialization FAILED πριν από writer/API creation.
> Branch/file ακόμη ABSENT. Κανένα rerun/repair. MASTER/schedule OFF.
> [Αιτία, failure evidence και απαιτούμενη ΝΕΑ έγκριση](docs/PRODUCTION_INITIALIZATION_EL.md).


Αυτόματες ανακοινώσεις για **DayZ / Infinity** και **Milo & Mia** στο ίδιο Discord
κανάλι, με ένα υπάρχον webhook. Python + GitHub Actions, χωρίς να μένει ανοικτό
το Windows PC. Τα μηνύματα και οι ρυθμίσεις αλλάζουν από το GitHub website ή VS Code.

**Τρέχουσα κατάσταση (2026-10-16):** ο isolated GitHub canary πέρασε14 actual
persistence checks σε δύο fresh hosted runners. Windows104 tests/14 filesystem
checks και Linux104 tests ανά job PASS. [Canary report](docs/DURABLE_CANARY_RESULTS.md).
Η disposable branch διατηρείται· και τα δύο εγκεκριμένα runs εξαντλήθηκαν.
Το προηγούμενο μοναδικό official API run πέρασε και για τις δύο YouTube πηγές,
2 requests/~2 units. [API report](docs/YOUTUBE_API_CLOUD_VALIDATION.md).
**MASTER/media OFF, schedule disabled.** Production notification-state ανέγγιχτο.
Production initialization/baseline, Discord και activation θέλουν ξεχωριστή έγκριση.
Δεν υπάρχει ακόμη production readiness. TikTok παραμένει experimental.

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
4. Production initialize/baseline και έλεγχος durable state απαιτούν ξεχωριστή
   έγκριση. Ο canary επαλήθευσε actual GitHub state μόνο στη disposable branch,
   χωρίς πρόσβαση στο notification-state.
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
