require 'rails_helper'

RSpec.describe DispatchMessage, type: :model do
  subject { build(:dispatch_message) }

  it { should belong_to(:account) }
  it { should belong_to(:dispatch) }
  it { should belong_to(:recipient) }

  it { should define_enum_for(:status).with_values(%i[pending sent failed delivered opened]) }

  it 'is valid with defaults' do
    expect(subject).to be_valid
  end

  it 'requires recipient_address' do
    subject.recipient_address = nil
    expect(subject).not_to be_valid
  end
end
