require 'rails_helper'

RSpec.describe Dispatch, type: :model do
  subject { build(:dispatch) }

  it { should belong_to(:account) }
  it { should belong_to(:user) }
  it { should belong_to(:reference).optional }
  it { should have_many(:dispatch_messages).dependent(:destroy) }

  it { should define_enum_for(:status).with_values(%i[pending processing completed failed]) }

  it 'is valid with defaults' do
    expect(subject).to be_valid
  end

  context 'with reference' do
    it 'accepts a job as reference' do
      dispatch = build(:dispatch, :with_job_reference)
      expect(dispatch.reference).to be_a(Job)
      expect(dispatch).to be_valid
    end
  end
end
