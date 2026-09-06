import admin from '@/locales/en/admin.json'
import auth from '@/locales/en/auth.json'
import briefing from '@/locales/en/briefing.json'
import caseDetail from '@/locales/en/caseDetail.json'
import common from '@/locales/en/common.json'
import evaluation from '@/locales/en/evaluation.json'
import ingest from '@/locales/en/ingest.json'
import menu from '@/locales/en/menu.json'
import queue from '@/locales/en/queue.json'
import review from '@/locales/en/review.json'

/**
 * One namespace per screen or shared vocabulary, so a key's home is obvious from where it is
 * read. `common` is first because it is the default namespace an untyped `useTranslation()`
 * resolves against.
 */
export default { common, menu, auth, review, queue, caseDetail, ingest, evaluation, admin, briefing }
