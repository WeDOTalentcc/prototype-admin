module TranslatedErrors
  extend ActiveSupport::Concern

  def translated_errors_for(record)
    {
      pt: I18n.with_locale(:pt) { record.errors.full_messages }
              .reject { |msg| msg.include?("translation missing") },
      en: I18n.with_locale(:en) { record.errors.full_messages }
    }
  end
end
