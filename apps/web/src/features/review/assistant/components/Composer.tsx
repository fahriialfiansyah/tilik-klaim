import { ArrowUp, Square } from 'lucide-react'
import { forwardRef, useImperativeHandle, useRef, useState, type KeyboardEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { ScopePicker } from '@/features/review/assistant/components/ScopePicker'
import { MAX_QUESTION_CHARS, type AssistantScope } from '@/features/review/assistant/types'
import type { QueueCasesState } from '@/features/review/assistant/useQueueCases'
import { cn } from '@/lib/utils'

/** Show the counter only as the limit approaches; a number that never matters is noise. */
const COUNTER_FROM = MAX_QUESTION_CHARS - 100
const MAX_INPUT_HEIGHT = 168

/**
 * The question input: text, the scope it will read, and send — or stop while an answer is
 * being prepared.
 *
 * Enter sends and Shift+Enter breaks the line, the convention every chat input shares. A
 * composition in progress (an IME choosing characters) is never sent by its own Enter. The
 * server's 500-character limit is enforced here first, so a reviewer is told before a request
 * is refused.
 */
export const Composer = forwardRef<
  HTMLTextAreaElement,
  {
    readonly scope: AssistantScope
    readonly queue: QueueCasesState
    readonly isBusy: boolean
    readonly onScopeChange: (scope: AssistantScope) => void
    /** Called once the scope menu has closed after a choice — where focus should go next. */
    readonly onScopeChosen?: () => void
    readonly onAsk: (question: string) => void
    readonly onStop: () => void
  }
>(function Composer({ scope, queue, isBusy, onScopeChange, onScopeChosen, onAsk, onStop }, ref) {
  const { t } = useTranslation('assistant')
  const [value, setValue] = useState('')
  const input = useRef<HTMLTextAreaElement>(null)
  // The page focuses the input after a suggestion is picked; it needs the same element.
  useImperativeHandle(ref, () => input.current as HTMLTextAreaElement, [])
  const question = value.trim()
  const isTooLong = value.length > MAX_QUESTION_CHARS
  const canSend = question.length > 0 && !isTooLong && !isBusy
  // The scope chip beside the input already names the case; the placeholder need not repeat it.
  const placeholder =
    scope.kind === 'CASE' ? t('composer.placeholderCase') : t('composer.placeholderQueue')

  const send = () => {
    if (!canSend) {
      return
    }
    onAsk(question)
    setValue('')
    if (input.current) {
      input.current.style.height = 'auto'
    }
  }

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Safari reports the Enter that ends an IME composition with keyCode 229 after the
    // composition has already closed, so `isComposing` alone would send a half-typed word.
    const isComposing = event.nativeEvent.isComposing || event.keyCode === 229
    if (event.key === 'Enter' && !event.shiftKey && !isComposing) {
      event.preventDefault()
      send()
    } else if (event.key === 'Escape' && isBusy) {
      event.preventDefault()
      onStop()
    }
  }

  return (
    <div>
      <div
        className={cn(
          'rounded-lg border bg-card shadow-panel transition-colors duration-[var(--motion-fast)]',
          // The ring belongs to the whole input — text, scope and send — not to the bare textarea
          // inside it, so the global focus ring is moved here from the textarea.
          isTooLong
            ? 'border-notice-line'
            : 'border-line-strong focus-within:border-brand focus-within:shadow-[0_0_0_3px_var(--a-1-soft)]',
        )}
      >
        <textarea
          ref={input}
          rows={1}
          value={value}
          aria-label={t('composer.label')}
          aria-describedby="asisten-petunjuk"
          aria-invalid={isTooLong}
          placeholder={placeholder}
          onChange={(event) => {
            setValue(event.target.value)
            // Grow with the text up to a ceiling, then scroll inside. Measured from `auto` so the
            // box shrinks back when text is deleted.
            event.target.style.height = 'auto'
            event.target.style.height = `${Math.min(event.target.scrollHeight, MAX_INPUT_HEIGHT)}px`
          }}
          onKeyDown={onKeyDown}
          className="block max-h-[168px] min-h-[52px] w-full resize-none bg-transparent px-[15px] pt-[14px] pb-[6px] text-body-lg text-ink outline-none placeholder:text-ink-3 focus-visible:shadow-none"
        />
        <div className="flex items-center justify-between gap-3 px-[10px] pb-[10px]">
          <ScopePicker
            scope={scope}
            queue={queue}
            isDisabled={isBusy}
            onChange={onScopeChange}
            onChosen={onScopeChosen}
          />
          <div className="flex shrink-0 items-center gap-3">
            {value.length >= COUNTER_FROM ? (
              <span
                data-numeric
                className={cn('font-mono text-meta', isTooLong ? 'text-notice' : 'text-ink-3')}
              >
                {t('composer.count', { count: value.length, max: MAX_QUESTION_CHARS })}
              </span>
            ) : null}
            {isBusy ? (
              <Button size="icon" variant="outline" onClick={onStop} aria-label={t('composer.stop')} title={t('composer.stop')}>
                <Square aria-hidden className="size-[13px] fill-current" />
              </Button>
            ) : (
              <Button size="icon" onClick={send} disabled={!canSend} aria-label={t('composer.send')} title={t('composer.send')}>
                <ArrowUp aria-hidden />
              </Button>
            )}
          </div>
        </div>
      </div>
      <p id="asisten-petunjuk" className="mt-[7px] flex flex-wrap justify-between gap-x-4 gap-y-1 text-meta text-ink-3">
        <span>{isTooLong ? t('composer.tooLong', { max: MAX_QUESTION_CHARS }) : t('composer.footnote')}</span>
        <span className="hidden sm:inline">{t('composer.hint')}</span>
      </p>
    </div>
  )
})
