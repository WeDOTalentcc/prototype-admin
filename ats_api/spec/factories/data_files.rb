# spec/factories/data_files.rb
FactoryBot.define do
  factory :data_file do
    association :user, factory: :user
    account_id { user.account.id }

    name { Faker::File.file_name(dir: 'docs', ext: 'pdf') }
    file_type { 'application/pdf' }
    reference_type { [ 'Message', 'Candidate', 'Job' ].sample }
    reference_id { Faker::Number.between(from: 1, to: 100) }
    is_deleted { false }
    is_downloaded { false }

    # Anexa um arquivo de teste padrão
    after(:build) do |data_file|
      unless data_file.file.attached?
        data_file.file.attach(
          io: File.open(Rails.root.join('spec', 'support', 'assets', 'example.pdf')),
          filename: 'example.pdf',
          content_type: 'application/pdf'
        )
      end
    end

    # Trait para um arquivo de imagem (se necessário)
    trait :image do
      name { Faker::File.file_name(dir: 'images', ext: 'png') }
      file_type { 'image/png' }
      after(:build) do |data_file|
        unless data_file.file.attached?
          data_file.file.attach(
            io: File.open(Rails.root.join('spec', 'support', 'assets', 'example.png')), # Crie este arquivo se usar
            filename: 'example.png',
            content_type: 'image/png'
          )
        end
      end
    end
  end
end
