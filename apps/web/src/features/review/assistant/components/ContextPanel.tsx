import { ArrowUpRight, Dot } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { shortId } from '@/features/review/assistant/conversation'
import { useGeneratedByLabel } from '@/features/review/assistant/labels'
import type { AssistantAnswer, AssistantScope } from '@/features/review/assistant/types'
import type { PositionedCase } from '@/features/review/assistant/useQueueCases'
import { BandBadge } from '@/features/review/shared/components/BandBadge'

const MICRO_LABEL = 'mb-[8px] font-mono text-micro font-semibold tracking-label text-ink-3'

function Block({ label, children }: { readonly label: string; readonly children: ReactNode }) {
  return (
    <section aria-label={label} className="border-b border-line px-[16px] py-[14px] last:border-b-0">
      <p className={MICRO_LABEL}>{label}</p>
      {children}
    </section>
  )
}

function Bullets({ items }: { readonly items: readonly string[] }) {
  return (
    <ul className="space-y-[5px]">
      {items.map((item) => (
        <li key={item} className="flex gap-[6px] text-small text-ink-2">
          <Dot aria-hidden className="-ml-[6px] size-[18px] shrink-0 text-ink-3" />
          <span className="text-pretty">{item}</span>
        </li>
      ))}
    </ul>
  )
}

/**
 * What the assistant can see, and what it will not do — the "model & context" panel the
 * reference kits put beside a conversation, filled with this product's actual limits.
 *
 * The limits are not decoration. They are ADR-0007's guarantees in the reviewer's words, beside
 * every answer, so nobody has to take the page's restraint on trust.
 */
export function ContextPanel({
  scope,
  scopeCase,
  lastAnswer,
}: {
  readonly scope: AssistantScope
  readonly scopeCase: PositionedCase | null
  readonly lastAnswer: AssistantAnswer | null
}) {
  const { t } = useTranslation('assistant')
  const generatedByLabel = useGeneratedByLabel()
  const reads = t(scope.kind === 'CASE' ? 'context.readsCase' : 'context.readsQueue', {
    returnObjects: true,
  }) as readonly string[]

  return (
    <aside
      aria-label={t('context.label')}
      className="hidden w-[300px] shrink-0 flex-col overflow-hidden rounded-lg border border-line bg-card shadow-panel xl:flex"
    >
      <PerfectScrollArea className="flex-1">
        <Block label={t('context.scope')}>
          {scope.kind === 'CASE' ? (
            <div>
              <p className="mb-[6px] flex flex-wrap items-center gap-2">
                <span data-numeric title={scope.case_id} className="font-mono text-small font-semibold text-ink">
                  {shortId(scope.case_id)}
                </span>
                {scopeCase ? <BandBadge band={scopeCase.row.band} className="px-[7px] py-[1px] text-meta" /> : null}
              </p>
              {scopeCase ? (
                <p className="mb-[8px] text-small text-ink-2 text-pretty">{scopeCase.row.reason_sentence}</p>
              ) : null}
              <Link
                to={`/cases/${encodeURIComponent(scope.case_id)}`}
                className="inline-flex items-center gap-1 text-small font-medium text-brand underline-offset-2 hover:underline"
              >
                {t('answer.openCase')}
                <ArrowUpRight aria-hidden className="size-[14px]" />
              </Link>
            </div>
          ) : (
            <p className="text-small text-ink-2 text-pretty">{t('context.queueScope')}</p>
          )}
        </Block>

        <Block label={t('context.reads')}>
          <Bullets items={reads} />
        </Block>

        <Block label={t('context.limits')}>
          <Bullets
            items={[
              t('context.limitCites'),
              t('context.limitVerdict'),
              t('context.limitDecision'),
              t('context.limitWrite'),
            ]}
          />
        </Block>

        <Block label={t('context.lastAnswer')}>
          <p data-numeric className="text-small text-ink-2">
            {lastAnswer
              ? `${generatedByLabel(lastAnswer.generated_by)}${lastAnswer.model_id ? ` · ${lastAnswer.model_id}` : ''}`
              : t('context.noAnswerYet')}
          </p>
          <p className="mt-[10px] text-meta text-ink-3 text-pretty">{t('context.memory')}</p>
        </Block>
      </PerfectScrollArea>
    </aside>
  )
}
