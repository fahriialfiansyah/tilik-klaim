import admin from '@/locales/id/admin.json'
import assistant from '@/locales/id/assistant.json'
import auth from '@/locales/id/auth.json'
import briefing from '@/locales/id/briefing.json'
import caseDetail from '@/locales/id/caseDetail.json'
import common from '@/locales/id/common.json'
import evaluation from '@/locales/id/evaluation.json'
import ingest from '@/locales/id/ingest.json'
import menu from '@/locales/id/menu.json'
import queue from '@/locales/id/queue.json'
import review from '@/locales/id/review.json'

/**
 * One namespace per screen or shared vocabulary, so a key's home is obvious from where it is
 * read. `common` is first because it is the default namespace an untyped `useTranslation()`
 * resolves against.
 */
export default { common, menu, auth, review, queue, caseDetail, ingest, evaluation, admin, briefing, assistant }
