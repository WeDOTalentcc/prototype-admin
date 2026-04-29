# spec/models/apply_spec.rb
require 'rails_helper'

RSpec.describe Apply, type: :model do
  describe 'associations' do
    it { should belong_to(:candidate) }
    it { should belong_to(:job) }
    it { should belong_to(:selective_process) }
  end

  describe 'defaults' do
    it 'sets is_deleted to false by default' do
      apply = described_class.new
      expect(apply.is_deleted).to eq(false)
    end
  end

   describe 'callbacks' do
    let(:user) { create(:user) }
    let(:account) { user.account }
    let(:candidate) { create(:candidate, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:selective_process_1) { create(:selective_process, account: account) }
    let(:selective_process_2) { create(:selective_process, account: account) }

    before do
      Current.user = user
    end

    it 'creates an ApplyStatus when selective_process_id changes' do
      apply = create(
        :apply,
        candidate: candidate,
        job: job,
        selective_process: selective_process_1,
        account_id: account.id
      )

      expect {
        apply.update!(selective_process: selective_process_2)
      }.to change(ApplyStatus, :count).by(1)

      status = ApplyStatus.last
      expect(status.apply).to eq(apply)
      expect(status.selective_process).to eq(selective_process_2)
      expect(status.user_id).to eq(user.id)
      expect(status.account_id).to eq(account.id)
    end

    it 'creates an ApplyStatus when selective_process_status changes' do
      apply = create(
        :apply,
        candidate: candidate,
        job: job,
        selective_process: selective_process_1,
        account_id: account.id,
        selective_process_status: 'Initial status'
      )

      expect {
        apply.update!(selective_process_status: 'New status')
      }.to change(ApplyStatus, :count).by(1)

      status = ApplyStatus.last
      expect(status.status_name).to eq('New status')
    end

    it 'does not create an ApplyStatus when other attributes change' do
      apply = create(
        :apply,
        candidate: candidate,
        job: job,
        selective_process: selective_process_1,
        account_id: account.id
      )

      expect {
        apply.update!(evaluation_candidate_status: :sent)
      }.not_to change(ApplyStatus, :count)
    end
  end

  describe "enqueue_screening_evaluations_if_needed" do
    let(:account) { create(:account, tenant: "public") }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account, is_screening_active: true) }
    let(:sp_screening) { create(:selective_process, job: job, account: account, status: :screening) }
    let(:sp_web) { create(:selective_process, job: job, account: account, status: :web_submission) }
    let(:candidate) { create(:candidate, account: account) }

    before { Apartment::Tenant.switch!(account.tenant) }
    after { Apartment::Tenant.switch!("public") }

    it "enqueues SendScreeningEvaluationsJob when apply is created in screening stage" do
      expect(Jobs::SendScreeningEvaluationsJob).to receive(:perform_async).with(job.id, account.id)

      create(:apply, job: job, candidate: candidate, selective_process: sp_screening, account: account)
    end

    it "enqueues SendScreeningEvaluationsJob when apply is moved to screening stage" do
      apply = create(:apply, job: job, candidate: candidate, selective_process: sp_web, account: account)

      expect(Jobs::SendScreeningEvaluationsJob).to receive(:perform_async).with(job.id, account.id)

      apply.update!(selective_process: sp_screening)
    end

    it "does not enqueue when job has is_screening_active false" do
      job.update!(is_screening_active: false)

      expect(Jobs::SendScreeningEvaluationsJob).not_to receive(:perform_async)

      create(:apply, job: job, candidate: candidate, selective_process: sp_screening, account: account)
    end

    it "does not enqueue when skip_screening_enqueue flag is set (bulk approve)" do
      expect(Jobs::SendScreeningEvaluationsJob).not_to receive(:perform_async)

      Thread.current[:skip_screening_enqueue] = true
      create(:apply, job: job, candidate: candidate, selective_process: sp_screening, account: account)
    ensure
      Thread.current[:skip_screening_enqueue] = false
    end
  end

  describe '.find_or_create_apply' do
    let(:user) { create(:user) }
    let(:account) { user.account }
    let(:candidate) { create(:candidate, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:selective_process) { create(:selective_process, account: account) }

    context 'when no apply exists' do
      it 'creates a new apply' do
        expect {
          Apply.find_or_create_apply(
            candidate_id: candidate.id,
            job_id: job.id,
            account_id: account.id,
            selective_process_id: selective_process.id,
            selective_process_status: 'Em análise',
            user_id: user.id
          )
        }.to change(Apply, :count).by(1)
      end
    end

    context 'when an apply exists with is_deleted = false' do
      let!(:existing_apply) do
        create(
          :apply,
          candidate: candidate,
          job: job,
          account: account,
          selective_process: selective_process,
          selective_process_status: 'Candidato',
          is_deleted: false
        )
      end

      it 'returns the existing apply and updates it' do
        result = Apply.find_or_create_apply(
          candidate_id: candidate.id,
          job_id: job.id,
          account_id: account.id,
          selective_process_id: selective_process.id,
          selective_process_status: 'Em análise',
          user_id: user.id
        )

        expect(result.id).to eq(existing_apply.id)
        expect(result.selective_process_status).to eq('Em análise')
        expect(Apply.count).to eq(1) # Não cria um novo
      end
    end

    context 'when an apply exists with is_deleted = true' do
      let!(:deleted_apply) do
        create(
          :apply,
          candidate: candidate,
          job: job,
          account: account,
          selective_process: selective_process,
          is_deleted: true
        )
      end

      it 'creates a new apply' do
        expect {
          Apply.find_or_create_apply(
            candidate_id: candidate.id,
            job_id: job.id,
            account_id: account.id,
            selective_process_id: selective_process.id,
            selective_process_status: 'Em análise',
            user_id: user.id
          )
        }.to change(Apply, :count).by(1)
      end
    end

    context 'when candidate_id or job_id is missing' do
      it 'returns nil when candidate_id is missing' do
        result = Apply.find_or_create_apply(
          candidate_id: nil,
          job_id: job.id,
          account_id: account.id
        )

        expect(result).to be_nil
      end

      it 'returns nil when job_id is missing' do
        result = Apply.find_or_create_apply(
          candidate_id: candidate.id,
          job_id: nil,
          account_id: account.id
        )

        expect(result).to be_nil
      end
    end

    context 'when selective_process_id is omitted but job has a web_submission stage' do
      let!(:sp_web) do
        create(
          :selective_process,
          job: job,
          account: account,
          name: 'Inscrição',
          status: :web_submission,
          position: 0
        )
      end

      it 'creates apply using the first web_submission selective process for the job' do
        expect {
          Apply.find_or_create_apply(
            candidate_id: candidate.id,
            job_id: job.id,
            account_id: account.id,
            selective_process_id: nil,
            selective_process_status: 'novo',
            user_id: user.id
          )
        }.to change(Apply, :count).by(1)

        apply = Apply.find_by(candidate_id: candidate.id, job_id: job.id, is_deleted: false)
        expect(apply.selective_process_id).to eq(sp_web.id)
      end
    end
  end

  describe '#get_candidate_feedback_type' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:candidate) { create(:candidate, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:selective_process) { create(:selective_process, account: account) }
    let(:apply) { create(:apply, candidate: candidate, job: job, account: account, selective_process: selective_process) }

    context 'when there is no feedback' do
      it 'returns nil' do
        expect(apply.get_candidate_feedback_type).to be_nil
      end
    end

    context 'when there is a like feedback' do
      before do
        create(:candidate_feedback,
          apply: apply,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'returns "like"' do
        expect(apply.get_candidate_feedback_type).to eq('like')
      end
    end

    context 'when there is a dislike feedback' do
      before do
        create(:candidate_feedback,
          apply: apply,
          user: user,
          account: account,
          feedback_type: 'dislike',
          is_deleted: false
        )
      end

      it 'returns "dislike"' do
        expect(apply.get_candidate_feedback_type).to eq('dislike')
      end
    end

    context 'when feedback is deleted' do
      before do
        create(:candidate_feedback,
          apply: apply,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: true
        )
      end

      it 'returns nil' do
        expect(apply.get_candidate_feedback_type).to be_nil
      end
    end
  end

  describe '#search_data' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:candidate) { create(:candidate, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:selective_process) { create(:selective_process, account: account) }
    let(:apply) { create(:apply, candidate: candidate, job: job, account: account, selective_process: selective_process) }

    it 'includes candidate_feedback field' do
      search_data = apply.search_data
      expect(search_data).to have_key(:candidate_feedback)
    end

    context 'with like feedback' do
      before do
        create(:candidate_feedback,
          apply: apply,
          user: user,
          account: account,
          feedback_type: 'like',
          is_deleted: false
        )
      end

      it 'includes the feedback type in search_data' do
        search_data = apply.search_data
        expect(search_data[:candidate_feedback]).to eq('like')
      end
    end
  end
end
