# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::CopyService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user, title: "Ruby Developer") }

  before do
    allow(ActionCable.server).to receive(:broadcast)
  end

  describe '#call' do
    context 'when job exists' do
      it 'creates a copy of the job' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        expect(result[:success]).to be true
        expect(result[:job]).to be_a(Job)
        expect(result[:job].title).to eq("Ruby Developer #1")
        expect(result[:job].source_job_id).to eq(job.id)
      end

      it 'resets job attributes' do
        job.update!(is_archived: true, is_active: false, external_id: "EXT123")

        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        new_job = result[:job]
        expect(new_job.is_archived).to be false
        expect(new_job.is_active).to be true
        expect(new_job.external_id).to be_nil
      end

      it 'increments copy counter' do
        described_class.new(job_id: job.id, user_id: user.id).call
        result = described_class.new(job_id: job.id, user_id: user.id).call

        expect(result[:job].title).to eq("Ruby Developer #2")
      end
    end

    context 'when job does not exist' do
      it 'returns error' do
        result = described_class.new(
          job_id: 99999,
          user_id: user.id
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to eq("Job not found")
      end
    end

    context 'when user does not exist' do
      it 'returns error' do
        result = described_class.new(
          job_id: job.id,
          user_id: 99999
        ).call

        expect(result[:success]).to be false
        expect(result[:error]).to eq("User not found")
      end
    end
  end

  describe '.copy_multiple' do
    context 'when amount is valid' do
      it 'creates multiple copies' do
        copy_count = 3

        result = described_class.copy_multiple(
          amount: copy_count,
          job_id: job.id,
          user_id: user.id
        )

        expect(result).not_to be_nil
        expect(result[:success]).to be true
        expect(result[:count]).to eq(copy_count)
      end

      it 'broadcasts progress updates' do
        described_class.copy_multiple(
          amount: 3,
          job_id: job.id,
          user_id: user.id
        )

        expect(ActionCable.server).to have_received(:broadcast)
          .with("job_copy:#{user.id}_job_copy_collection", hash_including(status: "loading"))
          .at_least(3).times
      end

      it 'broadcasts completion' do
        described_class.copy_multiple(
          amount: 2,
          job_id: job.id,
          user_id: user.id
        )

        expect(ActionCable.server).to have_received(:broadcast)
          .with("job_copy:#{user.id}_job_copy_collection", hash_including(status: "completed", percent: 100))
          .once
      end

      it 'includes copied job IDs in progress' do
        described_class.copy_multiple(
          amount: 2,
          job_id: job.id,
          user_id: user.id
        )

        expect(ActionCable.server).to have_received(:broadcast)
          .with("job_copy:#{user.id}_job_copy_collection", hash_including(:copied_job_ids))
          .at_least(2).times
      end
    end

    context 'when amount is zero' do
      it 'returns nil and does not create copies' do
        result = described_class.copy_multiple(
          amount: 0,
          job_id: job.id,
          user_id: user.id
        )

        expect(result).to be_nil
      end
    end

    context 'when amount is >= 100' do
      it 'returns nil and does not create copies' do
        result = described_class.copy_multiple(
          amount: 100,
          job_id: job.id,
          user_id: user.id
        )

        expect(result).to be_nil
      end
    end

    context 'when amount is nil' do
      it 'returns nil and does not create copies' do
        result = described_class.copy_multiple(
          amount: nil,
          job_id: job.id,
          user_id: user.id
        )

        expect(result).to be_nil
      end
    end
  end

  describe 'relationship copying' do
    context 'with direct relationships' do
      let!(:selective_process) do
        create(:selective_process,
          job: job,
          account: account,
          name: "Screening",
          status: :screening
        )
      end

      it 'copies selective processes' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        new_job = result[:job]
        expect(new_job.selective_processes.count).to eq(1)
        expect(new_job.selective_processes.first.name).to eq("Screening")
        expect(new_job.selective_processes.first.status).to eq("screening")
      end
    end

    context 'with polymorphic relationships' do
      let!(:language) { create(:language) }
      let!(:skill) { create(:skill, account: account) }
      let!(:benefit) { create(:benefit) }

      before do
        create(:language_relationship,
          reference: job,
          language: language,
          level: "fluente"
        )

        SkillRelationship.create!(
          reference: job,
          skill: skill,
          account: account,
          level_skill: 3,
          is_deleted: false
        )

        create(:benefit_relationship,
          reference: job,
          benefit: benefit
        )
      end

      it 'copies language relationships' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        new_job = result[:job]
        expect(new_job.language_relationships.count).to eq(1)
        expect(new_job.language_relationships.first.language_id).to eq(language.id)
        expect(new_job.language_relationships.first.level).to eq("fluente")
      end

      it 'copies skill relationships' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        new_job = result[:job]
        expect(new_job.skill_relationships.count).to eq(1)
        expect(new_job.skill_relationships.first.skill_id).to eq(skill.id)
        expect(new_job.skill_relationships.first.level_skill).to eq(3)
      end

      it 'copies benefit relationships' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        new_job = result[:job]
        expect(new_job.benefit_relationships.count).to eq(1)
        expect(new_job.benefit_relationships.first.benefit_id).to eq(benefit.id)
      end

      it 'copies all relationships together' do
        create(:selective_process,
          job: job,
          account: account,
          name: "Test Process",
          status: :screening
        )

        result = described_class.new(
          job_id: job.id,
          user_id: user.id
        ).call

        new_job = result[:job]
        expect(new_job.language_relationships.count).to eq(1)
        expect(new_job.skill_relationships.count).to eq(1)
        expect(new_job.benefit_relationships.count).to eq(1)
        expect(new_job.selective_processes.count).to eq(1)
      end
    end

    context 'with entities filter' do
      let!(:language) { create(:language) }

      before do
        create(:language_relationship,
          reference: job,
          language: language,
          level: "fluente"
        )
      end

      it 'copies only specified entities' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id,
          entities: [ "language_relationships" ]
        ).call

        new_job = result[:job]
        expect(new_job.language_relationships.count).to eq(1)
      end

      it 'skips unspecified entities' do
        result = described_class.new(
          job_id: job.id,
          user_id: user.id,
          entities: [ "other_relationships" ]
        ).call

        new_job = result[:job]
        expect(new_job.language_relationships.count).to eq(0)
      end
    end
  end
end
