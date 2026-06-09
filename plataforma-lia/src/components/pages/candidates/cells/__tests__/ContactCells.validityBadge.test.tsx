import React from 'react'
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { renderEmailCell, renderPhoneCell } from '../ContactCells'

const base = {
  id: 'c1', name: 'Ana', email: 'ana@empresa.com',
  source: 'local', pearch_profile_id: null, has_email: true,
} as any

describe('renderEmailCell — validity badge', () => {
  it('mostra CheckCircle2 verde quando email_valid=true', () => {
    const { container } = render(
      <>{renderEmailCell(base, {}, () => {}, undefined, { email_valid: true })}</>
    )
    const icon = container.querySelector('[aria-label="E-mail verificado"]')
    expect(icon).not.toBeNull()
    expect(icon?.getAttribute('class')).toContain('text-status-success')
  })

  it('mostra AlertTriangle amarelo quando email_valid=false', () => {
    const { container } = render(
      <>{renderEmailCell(base, {}, () => {}, undefined, { email_valid: false, email_reason: 'no_mx' })}</>
    )
    const icon = container.querySelector('[aria-label*="nao verificado"]')
    expect(icon).not.toBeNull()
    expect(icon?.getAttribute('class')).toContain('text-status-warning')
  })

  it('inclui razao no aria-label quando email_valid=false e reason presente', () => {
    const { container } = render(
      <>{renderEmailCell(base, {}, () => {}, undefined, { email_valid: false, email_reason: 'no_mx' })}</>
    )
    const icon = container.querySelector('[aria-label*="no_mx"]')
    expect(icon).not.toBeNull()
  })

  it('nao mostra badge quando email_valid=null', () => {
    const { container } = render(
      <>{renderEmailCell(base, {}, () => {}, undefined, { email_valid: null })}</>
    )
    expect(container.querySelector('[aria-label*="verificado"]')).toBeNull()
  })

  it('nao mostra badge quando validity nao fornecida', () => {
    const { container } = render(
      <>{renderEmailCell(base, {}, () => {}, undefined, undefined)}</>
    )
    expect(container.querySelector('[aria-label*="verificado"]')).toBeNull()
  })
})

describe('renderPhoneCell — validity badge', () => {
  const basePhone = { ...base, phone: '+5511999990000', has_phone: true } as any

  it('mostra CheckCircle2 verde quando phone_valid=true', () => {
    const { container } = render(
      <>{renderPhoneCell(basePhone, {}, () => {}, 'phone', undefined, { phone_valid: true })}</>
    )
    const icon = container.querySelector('[aria-label*="alido"]')
    expect(icon).not.toBeNull()
    expect(icon?.getAttribute('class')).toContain('text-status-success')
  })

  it('mostra AlertTriangle quando phone_valid=false', () => {
    const { container } = render(
      <>{renderPhoneCell(basePhone, {}, () => {}, 'phone', undefined, { phone_valid: false })}</>
    )
    const icon = container.querySelector('[aria-label*="nvalido"]')
    expect(icon).not.toBeNull()
    expect(icon?.getAttribute('class')).toContain('text-status-warning')
  })
})
