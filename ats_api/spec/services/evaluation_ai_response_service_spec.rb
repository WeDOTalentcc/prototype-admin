# frozen_string_literal: true

require 'rails_helper'

RSpec.describe EvaluationAiResponseService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job, is_chatbot: true, chatbot_channel: 'whatsapp') }
  let(:candidate) { create(:candidate, account: account, mobile_phone: '+5511999999999') }
  let(:apply) { create(:apply, job: job, candidate: candidate, account: account) }
  let(:evaluation_candidate) { create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, apply: apply, account: account, job: job, user: user) }
  let(:question) { create(:question, evaluation: evaluation, title: 'Test Question', description: 'Describe your experience') }
  let(:message) do
    create(:message,
           account: account,
           reference: candidate,
           content: 'Candidate response',
           entity: Message::ROLE_CANDIDATE,
           status: Message::STATUS_NOT_ANSWERED,
           evaluation: evaluation,
           apply: apply,
           metadata: { 'question_index' => 1, 'question_id' => question.id })
  end

  let(:original_payload) do
    {
      account_id: account.id,
      evaluation_candidate_id: evaluation_candidate.id,
      message_id: message.id,
      question_id: question.id,
      candidate_answer: 'Tenho 5 anos de experiência com React...'
    }
  end

  let(:ai_response_satisfactory) do
    {
      score: 0.85,
      is_answer_satisfactory: true,
      feedback_for_recruiter: 'Candidato demonstrou conhecimento sólido...',
      chat_ack: 'Ótimo! ',
      responded: true,
      changed_subject: false,
      response_to_candidate: 'Entendi, obrigado pela resposta detalhada.',
      followup_needed: false,
      followup_question: nil,
      next_question: nil,
      end: false,
      interested_job: true,
      interested_job_msg: nil,
      avoid_answer: false
    }
  end

  let(:ai_response_followup) do
    {
      score: 0.5,
      is_answer_satisfactory: false,
      feedback_for_recruiter: 'Resposta incompleta',
      chat_ack: nil,
      responded: true,
      changed_subject: false,
      response_to_candidate: 'Pode detalhar um pouco mais?',
      followup_needed: true,
      followup_question: 'Quais tecnologias específicas você utilizou?',
      next_question: nil,
      end: false,
      interested_job: true,
      interested_job_msg: nil,
      avoid_answer: false
    }
  end

  let(:ai_response_avoid) do
    {
      avoid_answer: true
    }
  end

  let(:ai_response_not_interested) do
    {
      score: 0.0,
      is_answer_satisfactory: false,
      feedback_for_recruiter: 'Candidato não demonstrou interesse',
      chat_ack: nil,
      responded: true,
      changed_subject: false,
      response_to_candidate: nil,
      followup_needed: false,
      followup_question: nil,
      next_question: nil,
      end: true,
      interested_job: false,
      interested_job_msg: 'Entendemos que não tem interesse. Obrigado!',
      avoid_answer: false
    }
  end

  let(:ai_response_changed_subject) do
    {
      score: 0.0,
      is_answer_satisfactory: false,
      feedback_for_recruiter: 'Candidato mudou de assunto',
      chat_ack: nil,
      responded: true,
      changed_subject: true,
      response_to_candidate: 'Entendo, mas precisamos focar na pergunta...',
      followup_needed: false,
      followup_question: nil,
      next_question: nil,
      end: false,
      interested_job: true,
      interested_job_msg: nil,
      avoid_answer: false
    }
  end

  before do
    Apartment::Tenant.switch!(account.tenant)
    allow(Meta::WhatsappService).to receive(:send_text_message).and_return(true)
    stub_wsi_response_extraction
  end

  describe '#call' do
    context 'with satisfactory answer' do
      subject do
        described_class.new(
          original_payload: original_payload,
          ai_response: ai_response_satisfactory,
          chatbot_channel: 'whatsapp'
        )
      end

      it 'creates an Answer record' do
        expect { subject.call }.to change(Answer, :count).by(1)
      end

      it 'returns success' do
        result = subject.call
        expect(result.success?).to be true
      end

      it 'updates message status to answered' do
        subject.call
        expect(message.reload.status).to eq(Message::STATUS_ANSWERED)
      end

      it 'includes answer_id in response data' do
        result = subject.call
        expect(result.data[:answer_id]).to be_present
      end

      it "persists deterministic analysis data and aggregate fields" do
        subject.call

        saved_answer = Answer.last
        expect(saved_answer.analysis_data).to be_a(Hash)
        expect(saved_answer.final_skill_score).to be_between(0.0, 10.0)

        ec = evaluation_candidate.reload
        expect(ec.wsi_classification).to be_present
        expect(ec.wsi_level).to be_present
        expect(ec.wsi_summary).to be_present
      end
    end

    context 'with followup needed' do
      subject do
        described_class.new(
          original_payload: original_payload,
          ai_response: ai_response_followup,
          chatbot_channel: 'whatsapp'
        )
      end

      it 'creates an Answer record' do
        expect { subject.call }.to change(Answer, :count).by(1)
      end

      it 'returns success with next_question_sent' do
        result = subject.call
        expect(result.success?).to be true
        expect(result.data[:next_question_sent]).to be true
      end

      it 'sends WhatsApp message with followup' do
        subject.call
        expect(Meta::WhatsappService).to have_received(:send_text_message)
          .with(candidate.mobile_phone, anything)
      end
    end

    context 'with avoid_answer' do
      subject do
        described_class.new(
          original_payload: original_payload,
          ai_response: ai_response_avoid,
          chatbot_channel: 'internal'
        )
      end

      it 'does not create an Answer record' do
        expect { subject.call }.not_to change(Answer, :count)
      end

      it 'returns success with avoided flag' do
        result = subject.call
        expect(result.success?).to be true
        expect(result.data[:avoided]).to be true
      end
    end

    context 'with not interested candidate' do
      subject do
        described_class.new(
          original_payload: original_payload,
          ai_response: ai_response_not_interested,
          chatbot_channel: 'whatsapp'
        )
      end

      it 'marks evaluation as completed' do
        subject.call
        expect(evaluation_candidate.reload.completed).to be true
      end

      it 'returns finished: true' do
        result = subject.call
        expect(result.data[:finished]).to be true
      end
    end

    context 'with changed subject' do
      subject do
        described_class.new(
          original_payload: original_payload,
          ai_response: ai_response_changed_subject,
          chatbot_channel: 'whatsapp'
        )
      end

      it 'does not create an Answer record' do
        expect { subject.call }.not_to change(Answer, :count)
      end

      it 'creates a Message with the response' do
        expect { subject.call }.to change(Message, :count).by(1)
      end

      it 'sends WhatsApp message' do
        subject.call
        expect(Meta::WhatsappService).to have_received(:send_text_message)
          .with(candidate.mobile_phone, ai_response_changed_subject[:response_to_candidate])
      end
    end

    context 'with invalid account_id' do
      let(:invalid_payload) do
        original_payload.merge(account_id: 999999)
      end

      subject do
        described_class.new(
          original_payload: invalid_payload,
          ai_response: ai_response_satisfactory,
          chatbot_channel: 'whatsapp'
        )
      end

      it 'returns failure' do
        result = subject.call
        expect(result.success?).to be false
        expect(result.error).to include('find')
      end
    end

    context 'with invalid evaluation_candidate_id' do
      let(:invalid_payload) do
        original_payload.merge(evaluation_candidate_id: 999999)
      end

      subject do
        described_class.new(
          original_payload: invalid_payload,
          ai_response: ai_response_satisfactory,
          chatbot_channel: 'whatsapp'
        )
      end

      it 'returns failure' do
        result = subject.call
        expect(result.success?).to be false
      end
    end
  end
end
