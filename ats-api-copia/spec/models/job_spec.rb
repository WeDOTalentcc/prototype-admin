require 'rails_helper'

RSpec.describe Job, type: :model do
  subject { build(:job) }

  it { should belong_to(:user) }
  it { should belong_to(:account).optional }
  it { should have_many(:selective_processes).dependent(:destroy) }

  it { should validate_presence_of(:title) }
  it { should validate_presence_of(:description) }

  it 'has a valid factory' do
    expect(subject).to be_valid
  end

  describe 'after create' do
    let(:job) { create(:job) }

    it 'creates the default selective processes' do
      expect(job.selective_processes.count).to eq(5)

      expected_statuses = %w[
        web_submission
        screening
        interview
        rejected
        hired
      ]

      actual_statuses = job.selective_processes.order(:position).pluck(:status)
      expect(actual_statuses).to eq(expected_statuses)

      expected_names = [
        "Inscrição Web",
        "Triagem",
        "Entrevista",
        "Rejeitados",
        "Contratados"
      ]

      actual_names = job.selective_processes.order(:position).pluck(:name)
      expect(actual_names).to eq(expected_names)
    end
  end
end
